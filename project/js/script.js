document.addEventListener("DOMContentLoaded", () => {
  const header = document.querySelector(".site-header");
  const pageParticles = document.getElementById("page-particles");
  const revealTargets = document.querySelectorAll("[data-reveal]");
  const navLinks = document.querySelectorAll(".site-nav a");
  const navToggle = document.querySelector(".nav-toggle");
  const siteNav = document.querySelector(".site-nav");
  const year = document.getElementById("year");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (year) {
    year.textContent = new Date().getFullYear();
  }

  let lastScrollY = window.scrollY;

  const updateHeaderState = () => {
    if (!header) return;
    const currentScrollY = window.scrollY;

    header.classList.toggle("is-scrolled", currentScrollY > 12);

    if (currentScrollY > lastScrollY && currentScrollY > 80) {
      header.classList.add("is-hidden");
    } else {
      header.classList.remove("is-hidden");
    }

    lastScrollY = currentScrollY;
  };

  updateHeaderState();
  window.addEventListener("scroll", updateHeaderState, { passive: true });

  if (navToggle && siteNav) {
    const closeNav = () => {
      siteNav.classList.remove("is-open");
      navToggle.classList.remove("is-active");
      navToggle.setAttribute("aria-expanded", "false");
    };

    navToggle.addEventListener("click", () => {
      const isOpen = siteNav.classList.toggle("is-open");
      navToggle.classList.toggle("is-active", isOpen);
      navToggle.setAttribute("aria-expanded", String(isOpen));
    });

    siteNav.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", closeNav);
    });
  }

  if (pageParticles && window.tsParticles && !reduceMotion) {
    const initPageParticles = async () => {
      if (typeof window.loadSnowPreset === "function") {
        await window.loadSnowPreset(window.tsParticles);
      }

      await window.tsParticles.load({
        id: "page-particles",
        options: {
          fullScreen: {
            enable: false,
          },
          background: {
            color: {
              value: "transparent",
            },
          },
          fpsLimit: 60,
          detectRetina: true,
          pauseOnBlur: true,
          pauseOnOutsideViewport: true,
          preset: "snow",
          particles: {
            color: {
              value: ["#f3d9b8", "#e9c6a0", "#f7ece0"],
            },
            move: {
              enable: true,
              direction: "bottom",
              speed: 0.5,
              random: true,
              straight: false,
              outModes: {
                default: "out",
              },
            },
            number: {
              value: 38,
              density: {
                enable: true,
                area: 900,
              },
            },
            opacity: {
              value: {
                min: 0.2,
                max: 0.55,
              },
            },
            shape: {
              type: "circle",
            },
            size: {
              value: {
                min: 2,
                max: 6,
              },
            },
          },
          responsive: [
            {
              maxWidth: 720,
              options: {
                particles: {
                  move: {
                    speed: 0.45,
                  },
                  number: {
                    value: 30,
                  },
                  size: {
                    value: {
                      min: 1.5,
                      max: 4.4,
                    },
                  },
                },
              },
            },
          ],
        }
      });
    };

    initPageParticles().catch((error) => {
        console.error("tsParticles could not be initialized.", error);
      });
  }

  if (reduceMotion) {
    revealTargets.forEach((element) => element.classList.add("is-visible"));
  } else {
    const revealObserver = new IntersectionObserver(
      (entries, observer) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      },
      {
        threshold: 0.18,
        rootMargin: "0px 0px -8% 0px",
      }
    );

    revealTargets.forEach((element) => revealObserver.observe(element));
  }

  if (!navLinks.length) return;

  const currentPage = location.pathname.split("/").pop() || "index.html";

  navLinks.forEach((link) => {
    const href = link.getAttribute("href");
    link.classList.toggle("is-active", href === currentPage);
  });
});
