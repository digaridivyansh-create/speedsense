const howItWorksButton =
    document.querySelector(".btn-outline");

if (howItWorksButton) {
    howItWorksButton.addEventListener("click", function () {

        const features = document.querySelector("#features");

        if (features) {
            features.scrollIntoView({
                behavior: "smooth"
            });
        }

    });
}
