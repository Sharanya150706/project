
document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebarOverlay");
    const openButton = document.getElementById("menuToggle");
    const closeButton = document.getElementById("sidebarClose");

    if (!sidebar || !overlay) return;

    function openSidebar() {
        sidebar.classList.add("sidebar-open");
        overlay.classList.add("show");
        document.body.classList.add("bn-sidebar-visible");

        if (openButton) {
            openButton.setAttribute("aria-expanded", "true");
        }
    }

    function closeSidebar() {
        sidebar.classList.remove("sidebar-open");
        overlay.classList.remove("show");
        document.body.classList.remove("bn-sidebar-visible");

        if (openButton) {
            openButton.setAttribute("aria-expanded", "false");
        }
    }

    if (openButton) {
        openButton.setAttribute("aria-controls", "sidebar");
        openButton.setAttribute("aria-expanded", "false");

        openButton.addEventListener("click", function () {
            if (sidebar.classList.contains("sidebar-open")) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
    }

    if (closeButton) {
        closeButton.addEventListener("click", closeSidebar);
    }

    overlay.addEventListener("click", closeSidebar);

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") closeSidebar();
    });

    sidebar.querySelectorAll("a").forEach(function (link) {
        link.addEventListener("click", function () {
            if (window.innerWidth <= 900) closeSidebar();
        });
    }

    window.addEventListener("resize", function () {
        if (window.innerWidth > 900) closeSidebar();
    });
});
