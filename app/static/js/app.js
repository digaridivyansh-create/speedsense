/* =========================================
   SPENDSENSE JAVASCRIPT
========================================= */

console.log("SpendSense JavaScript loaded");


/* =========================================
   SEE HOW IT WORKS
========================================= */

const howItWorksButton =
    document.querySelector(".btn-outline");

howItWorksButton.addEventListener("click", function () {

    document.querySelector("#features").scrollIntoView({
        behavior: "smooth"
    });

});


/* =========================================
   SCROLL REVEAL
========================================= */

const revealElements =
    document.querySelectorAll(
        ".problem-card, .feature-card, .privacy-items div"
    );


const revealObserver =
    new IntersectionObserver(
        function (entries) {

            entries.forEach(function (entry) {

                if (entry.isIntersecting) {

                    entry.target.classList.add("visible");

                    revealObserver.unobserve(
                        entry.target
                    );

                }

            });

        },
        {
            threshold: 0.15
        }
    );


revealElements.forEach(function (element) {

    element.classList.add("reveal");

    revealObserver.observe(element);

});


/* =========================================
   BUTTON PRESS EFFECT
========================================= */

const buttons =
    document.querySelectorAll(".btn");


buttons.forEach(function (button) {

    button.addEventListener("click", function () {

        button.classList.add("clicked");

        setTimeout(function () {

            button.classList.remove("clicked");

        }, 180);

    });

});


/* =========================================
   FINANCIAL HEALTH ANIMATION
========================================= */

function animateNumber(
    element,
    start,
    end,
    duration
) {

    const startTime = performance.now();


    function update(currentTime) {

        const elapsed =
            currentTime - startTime;

        const progress =
            Math.min(
                elapsed / duration,
                1
            );


        const value =
            Math.floor(
                start +
                (end - start) * progress
            );


        element.textContent = value;


        if (progress < 1) {

            requestAnimationFrame(update);

        }

    }


    requestAnimationFrame(update);
}


const healthScore =
    document.querySelector(".health-score");


if (healthScore) {

    healthScore.textContent = "0";


    setTimeout(function () {

        animateNumber(
            healthScore,
            0,
            78,
            1200
        );

    }, 300);

}


/* =========================================
   NAVBAR SCROLL EFFECT
========================================= */

const navbar =
    document.querySelector(".navbar");


window.addEventListener("scroll", function () {

    if (window.scrollY > 30) {

        navbar.classList.add("navbar-scrolled");

    } else {

        navbar.classList.remove("navbar-scrolled");

    }

});


/* =========================================
   HERO MOUSE MOTION
========================================= */

const heroVisual =
    document.querySelector(".hero-visual");


if (heroVisual) {

    heroVisual.addEventListener(
        "mousemove",
        function (event) {

            const rect =
                heroVisual.getBoundingClientRect();


            const x =
                (event.clientX - rect.left)
                / rect.width
                - 0.5;


            const y =
                (event.clientY - rect.top)
                / rect.height
                - 0.5;


            const dashboard =
                document.querySelector(
                    ".dashboard-card"
                );


            dashboard.style.transform =
                `
                rotateY(${x * 8}deg)
                rotateX(${y * -8}deg)
                rotate(3deg)
                `;

        }
    );


    heroVisual.addEventListener(
        "mouseleave",
        function () {

            const dashboard =
                document.querySelector(
                    ".dashboard-card"
                );


            dashboard.style.transform =
                "rotate(3deg)";

        }
    );

}
/* =========================================================
   SPENDSENSE MOTION ENGINE
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    /* ---------- Scroll reveal ---------- */

    const revealElements =
        document.querySelectorAll(
            ".feature-card, .metric-card, .stat-card, section"
        );

    const revealObserver =
        new IntersectionObserver(
            (entries) => {

                entries.forEach((entry) => {

                    if (entry.isIntersecting) {

                        entry.target.classList.add(
                            "visible"
                        );

                    }

                });

            },
            {
                threshold: 0.12
            }
        );

    revealElements.forEach((element) => {

        element.classList.add("reveal");

        revealObserver.observe(element);

    });


    /* ---------- Button ripple ---------- */

    document
        .querySelectorAll(".btn")
        .forEach((button) => {

            button.addEventListener(
                "click",
                function (event) {

                    const ripple =
                        document.createElement("span");

                    const rect =
                        this.getBoundingClientRect();

                    const size =
                        Math.max(
                            rect.width,
                            rect.height
                        );

                    ripple.style.position = "absolute";
                    ripple.style.width = `${size}px`;
                    ripple.style.height = `${size}px`;
                    ripple.style.left =
                        `${event.clientX - rect.left - size / 2}px`;
                    ripple.style.top =
                        `${event.clientY - rect.top - size / 2}px`;

                    ripple.style.borderRadius = "50%";
                    ripple.style.background =
                        "rgba(255,255,255,.25)";
                    ripple.style.pointerEvents = "none";

                    ripple.animate(
                        [
                            {
                                transform: "scale(0)",
                                opacity: 1
                            },
                            {
                                transform: "scale(1)",
                                opacity: 0
                            }
                        ],
                        {
                            duration: 500,
                            easing: "ease-out"
                        }
                    );

                    this.appendChild(ripple);

                    setTimeout(
                        () => ripple.remove(),
                        500
                    );

                }
            );

        });


    /* ---------- Subtle cursor movement ---------- */

    const heroVisual =
        document.querySelector(
            ".hero-card, .dashboard-card"
        );

    if (heroVisual) {

        document.addEventListener(
            "mousemove",
            (event) => {

                const x =
                    (event.clientX /
                        window.innerWidth - .5);

                const y =
                    (event.clientY /
                        window.innerHeight - .5);

                heroVisual.style.transform =
                    `
                    translateY(-5px)
                    rotateY(${x * 4}deg)
                    rotateX(${y * -3}deg)
                    `;

            }
        );

        document.addEventListener(
            "mouseleave",
            () => {

                heroVisual.style.transform = "";

            }
        );

    }

});