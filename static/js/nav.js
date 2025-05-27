const menuBtn = document.querySelector('.nav-menu')
const menuBtnSvg = menuBtn.querySelectorAll('svg')
const nav = document.querySelector('.nav-content')


menuBtn.addEventListener('click', () => {
    nav.classList.toggle('nav-content-open')

    menuBtnSvg.forEach(svg => {
        svg.classList.toggle("deactivate")
    })
})