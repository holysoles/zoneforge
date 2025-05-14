from flask_restx import Namespace, Resource, reqparse
from werkzeug.exceptions import *  # pylint: disable=wildcard-import,unused-wildcard-import,redefined-builtin

from zoneforge.api import api_release_access
from zoneforge.db import db
from zoneforge.db.db_model import Group, Role, User

api = Namespace("rbac", description="RBAC Manager")

# Parsers
rbac_parser = reqparse.RequestParser(bundle_errors=True)
rbac_parser.add_argument("name", type=str, help="Missing name", required=True)


@api.route("/group")
class GroupResource(Resource):
    @api_release_access("group_read")
    def get(self):
        group_entities = db.paginate(db.select(Group))

        return {
            "groups": [
                {"id": group.id, "group_name": group.name} for group in group_entities
            ]
        }, 200

    @api_release_access("group_create")
    def post(self):
        args = rbac_parser.parse_args()
        group_name = args.get("name")

        group_entity = db.session.execute(
            db.select(Group).filter_by(name=group_name)
        ).scalar_one_or_none()

        if group_entity:
            raise Conflict("Group name already exist")

        group = Group(name=group_name)

        db.session.add(group)
        db.session.commit()

        return {"message": "Group created successfully"}, 201


@api.route("/group/<int:group_id>")
class SpecificGroupResource(Resource):
    @api_release_access("group_update")
    def put(self, group_id: int = None):
        args = rbac_parser.parse_args()
        group_name = args.get("name")

        group_entity = db.session.execute(
            db.select(Group).filter_by(name=group_name)
        ).scalar_one_or_none()

        if group_entity and group_entity.id == int(group_id):
            raise Conflict("This group already have this name")

        if group_entity:
            raise Conflict("Group name already exist")

        current_group = db.get_or_404(Group, group_id, description="Group id not exist")

        current_group.name = group_name

        db.session.commit()

        return {"message": "Group updated successfully"}, 200

    @api_release_access("group_delete")
    def delete(self, group_id: int = None):
        group_entity = db.get_or_404(Group, group_id, description="Group id not exist")

        db.session.delete(group_entity)
        db.session.commit()

        return {"message": "Group deleted"}, 200


@api.route("/role")
class RoleResource(Resource):
    @api_release_access("role_read")
    def get(self):
        role_entities = db.paginate(db.select(Role))

        return {
            "roles": [{"id": role.id, "role_name": role.name} for role in role_entities]
        }

    @api_release_access("role_create")
    def post(self):
        args = rbac_parser.parse_args()
        role_name = args.get("name")

        role_entity = db.session.execute(
            db.select(Role).filter_by(name=role_name)
        ).scalar_one_or_none()

        if role_entity:
            raise Conflict("Role name already exist")

        role = Role(name=role_name)

        db.session.add(role)
        db.session.commit()

        return {"message": "Role created successfully"}, 201


@api.route("/role/<int:role_id>")
class SpecificRoleResource(Resource):
    @api_release_access("role_update")
    def put(self, role_id: int = None):
        args = rbac_parser.parse_args()
        role_name = args.get("name")

        role_entity = db.session.execute(
            db.select(Role).filter_by(name=role_name)
        ).scalar_one_or_none()

        if role_entity and role_entity.id == role_id:
            raise Conflict("This role already have this name")

        if role_entity:
            raise Conflict("Role name already exist")

        current_role = db.get_or_404(Role, role_id, description="Role id not exist")

        current_role.name = role_name

        db.session.commit()

        return {"message": "Role updated successfully"}, 200

    @api_release_access("role_delete")
    def delete(self, role_id: int = None):
        role_entity = db.get_or_404(Role, role_id, description="Role id not exist")

        db.session.delete(role_entity)
        db.session.commit()

        return {"message": "Role deleted"}, 200


@api.route("/group/<int:group_id>/user/<int:user_id>")
class UserAssignGroupResource(Resource):
    @api_release_access("userAssignGroup_read")
    def post(self, group_id: int = None, user_id: int = None):
        db.get_or_404(Group, group_id, description="Group id not exist")
        user_entity = db.get_or_404(User, user_id, description="User id not exist")

        if user_entity.group_id:
            raise Conflict("User already assign to a group")

        user_entity.group_id = group_id

        db.session.commit()

        return {"message": "User assign to a group successfully"}, 200

    @api_release_access("userAssignGroup_update")
    def put(self, group_id: int = None, user_id: int = None):
        db.get_or_404(Group, group_id, description="Group id not exist")
        user_entity = db.get_or_404(User, user_id, description="User id not exist")

        if not user_entity.group_id:
            raise BadRequest("User not assign to any group")

        if user_entity.group.id == group_id:
            raise Conflict("User already assign to this group")

        user_entity.group_id = group_id

        db.session.commit()

        return {"message": "User assign to the new group"}, 200

    @api_release_access("userAssignGroup_delete")
    def delete(self, group_id: int = None, user_id: int = None):
        db.get_or_404(Group, group_id, description="Group id not exist")
        user_entity = db.get_or_404(User, user_id, description="User id not exist")

        if not user_entity.group_id:
            raise BadRequest("User not assign to any group")

        if user_entity.group.id != group_id:
            raise Conflict("User not assign to this group")

        user_entity.group_id = None

        db.session.commit()

        return {"message": "User association from this group deleted"}, 200


@api.route("/group/<int:group_id>/role/<int:role_id>")
class RoleAssignGroupResource(Resource):
    @api_release_access("roleAssignGroup_read")
    def post(self, group_id: int = None, role_id: int = None):
        group_entity = db.get_or_404(Group, group_id, description="Group id not exist")
        role_entity = db.get_or_404(Role, role_id, description="Role id not exist")

        for role in group_entity.roles:
            if role.id == role_id:
                raise Conflict("Role already assign to this group")

        group_entity.roles.append(role_entity)

        db.session.commit()

        return {"message": "Role assign to group successfully"}, 201

    @api_release_access("roleAssignGroup_delete")
    def delete(self, group_id: str = None, role_id: str = None):
        group_entity = db.get_or_404(Group, group_id, description="Group id not exist")
        role_entity = db.get_or_404(Role, role_id, description="Role id not exist")

        if role_entity not in group_entity.roles:
            raise Conflict("Role not a assign to this group")

        group_entity.roles.remove(role_entity)

        db.session.commit()

        return {"message": "Role association from this group deleted"}, 200
