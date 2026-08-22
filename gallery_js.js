/* =========================================
   ROSE GALLERY
   Gallery data comes from Flask backend
========================================= */

const galleryContainer =
    document.getElementById(
        "galleryContainer"
    );

const imageViewer =
    document.getElementById(
        "imageViewer"
    );

const viewerImage =
    document.getElementById(
        "viewerImage"
    );

const viewerTitle =
    document.getElementById(
        "viewerTitle"
    );

const viewerClose =
    document.getElementById(
        "viewerClose"
    );


/* =========================================
   LOAD GALLERY DATA
========================================= */

fetch("/api/gallery")
    .then(response => {

        if (!response.ok) {

            throw new Error(
                "Unable to load gallery."
            );
        }

        return response.json();
    })

    .then(data => {

        console.log(
            "Gallery data loaded:",
            data
        );

        galleryContainer.innerHTML = "";

        if (
            !data.sections ||
            data.sections.length === 0
        ) {

            galleryContainer.innerHTML = `
                <div
                    style="
                        padding:50px;
                        text-align:center;
                    "
                >
                    <h2>
                        No gallery images available.
                    </h2>
                </div>
            `;

            return;
        }


        /* =========================================
           CREATE EVERY SECTION
        ========================================= */

        data.sections.forEach(
            section => {

                const sectionElement =
                    document.createElement(
                        "section"
                    );

                sectionElement.className =
                    "gallery-section";

                sectionElement.id =
                    section.id;


                /* =========================================
                   SECTION HEADING
                ========================================= */

                sectionElement.innerHTML = `
                    <div class="section-heading">
                        <h2>
                            ${section.title}
                        </h2>
                    </div>

                    <div class="photo-grid"></div>
                `;


                const photoGrid =
                    sectionElement.querySelector(
                        ".photo-grid"
                    );


                /* =========================================
                   ADD PHOTOS
                ========================================= */

                if (
                    !section.photos ||
                    section.photos.length === 0
                ) {

                    return;
                }

                section.photos.forEach(
                    photo => {

                        const photoCard =
                            document.createElement(
                                "div"
                            );

                        photoCard.className =
                            "photo-card";


                        const image =
                            document.createElement(
                                "img"
                            );

                        image.src =
                            photo.file;

                        image.alt =
                            photo.title || section.title;

                        image.loading =
                            "lazy";


                        const photoTitle =
                            document.createElement(
                                "div"
                            );

                        photoTitle.className =
                            "photo-title";

                        photoTitle.textContent =
                            photo.title || section.title;


                        photoCard.appendChild(
                            image
                        );

                        photoCard.appendChild(
                            photoTitle
                        );


                        /* =========================================
                           OPEN IMAGE VIEWER
                        ========================================= */

                        photoCard.addEventListener(
                            "click",
                            () => {

                                viewerImage.src =
                                    photo.file;

                                viewerImage.alt =
                                    photo.title || section.title;

                                viewerTitle.textContent =
                                    photo.title || section.title;

                                imageViewer.classList.add(
                                    "show"
                                );
                            }
                        );


                        photoGrid.appendChild(
                            photoCard
                        );
                    }
                );

                galleryContainer.appendChild(
                    sectionElement
                );
            }
        );
    })

    .catch(error => {

        console.error(
            "Gallery Error:",
            error
        );

        galleryContainer.innerHTML = `
            <div
                style="
                    padding:50px;
                    text-align:center;
                "
            >
                <h2>
                    Gallery data could not be loaded.
                </h2>

                <p>
                    ${error.message}
                </p>
            </div>
        `;
    });


/* =========================================
   CLOSE IMAGE VIEWER
========================================= */

viewerClose.addEventListener(
    "click",
    () => {

        imageViewer.classList.remove(
            "show"
        );
    }
);


/* =========================================
   CLOSE WHEN CLICKING OUTSIDE IMAGE
========================================= */

imageViewer.addEventListener(
    "click",
    event => {

        if (
            event.target === imageViewer
        ) {

            imageViewer.classList.remove(
                "show"
            );
        }
    }
);


/* =========================================
   CLOSE USING ESC KEY
========================================= */

document.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Escape"
        ) {

            imageViewer.classList.remove(
                "show"
            );
        }
    }
);