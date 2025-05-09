// features/video/videoList.js

import showToast from "../../modules/toast.js";

export async function updateVideoList() {
    const videoListContainer = document.getElementById('videoList');
    if (!videoListContainer) return;

    createPlaceholderCards(6);

    try {
        const response = await fetch('/getVideosOfUser', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const result = await response.json();
            showToast(result.error || "Error fetching videos.", "error");
            return;
        }

        const data = await response.json();

        if (data.length === 0) {
            videoListContainer.innerHTML = '<div class="alert alert-info text-center">No videos found. Please upload a video.</div>';
            return;
        }

        videoListContainer.innerHTML = '';

        data.forEach(video => {
            const filenameWithoutExt = video.filename.split('.').slice(0, -1).join('.');
            const title = filenameWithoutExt.length > 30 ? filenameWithoutExt.substring(0, 30) + '...' : filenameWithoutExt;

            const videoCard = `
                <div class="col-12 col-md-6 col-lg-4">
                    <div class="card mb-3 d-flex flex-row align-items-center justify-content-between video-card" data-id="${video.id}">
                        <div class="w-100">
                            <div class="video-thumbnail-wrapper" style="width: 100%; height: 210px; border-radius: 10px; overflow: hidden; position: relative;">
                                <img src="/getThumbnail/${video.id}" alt="Video Thumbnail"
                                     loading="lazy"
                                     style="width: 100%; height: 210px; object-fit: cover; border-radius: 10px; background: #adb5bd;"
                                     onerror="this.style.display='none';this.parentNode.innerHTML='<div style=&quot;width:100%;height:210px;display:flex;align-items:center;justify-content:center;background:#adb5bd;color:#fff;font-weight:bold;font-size:1.2rem;border-radius:10px;&quot;>[No thumbnail]</div>';">
                            </div>
                            <div class="p-3">
                                <h5 class="mb-1">${title}</h5>
                                <small>Date: ${video.date_added}</small>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            videoListContainer.insertAdjacentHTML('beforeend', videoCard);
        });
    } catch (error) {
        console.error('Error fetching videos:', error);
        videoListContainer.innerHTML = '<div class="alert alert-danger text-center">Failed to load videos.</div>';
    }
}

export function createPlaceholderCards(count) {
    const videoListContainer = document.getElementById('videoList');
    if (!videoListContainer) return;

    videoListContainer.innerHTML = '';
    for (let i = 0; i < count; i++) {
        const placeholderCard = `
            <div class="col-12 col-md-6 col-lg-4">
                <div class="card mb-3">
                    <div class="w-100">
                        <div class="placeholder-glow" style="width: 100%; height: 210px; border-radius: 10px; background-color: #e9ecef;">
                            <span class="placeholder col-12 h-100"></span>
                        </div>
                        <div class="p-3">
                            <h5 class="card-title placeholder-glow">
                                <span class="placeholder col-6"></span>
                            </h5>
                            <p class="card-text placeholder-glow">
                                <span class="placeholder col-7"></span>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        videoListContainer.insertAdjacentHTML('beforeend', placeholderCard);
    }
}

export function appendVideoCard(video, prepend = false) {
    const videoListContainer = document.getElementById('videoList');
    if (!videoListContainer || !video) return;

    const filenameWithoutExt = video.filename.split('.').slice(0, -1).join('.');
    const title = filenameWithoutExt.length > 30 ? filenameWithoutExt.substring(0, 30) + '...' : filenameWithoutExt;

    const videoCard = `
        <div class="col-12 col-md-6 col-lg-4">
            <div class="card mb-3 d-flex flex-row align-items-center justify-content-between video-card" data-id="${video.id}">
                <div class="w-100">
                    <div class="video-thumbnail-wrapper" style="width: 100%; height: 210px; border-radius: 10px; overflow: hidden; position: relative;">
                        <img src="/getThumbnail/${video.id}" alt="Video Thumbnail"
                             loading="lazy"
                             style="width: 100%; height: 210px; object-fit: cover; border-radius: 10px; background: #adb5bd;"
                             onerror="this.style.display='none';this.parentNode.innerHTML='<div style=&quot;width:100%;height:210px;display:flex;align-items:center;justify-content:center;background:#adb5bd;color:#fff;font-weight:bold;font-size:1.2rem;border-radius:10px;&quot;>[No thumbnail]</div>';">
                    </div>
                    <div class="p-3">
                        <h5 class="mb-1">${title}</h5>
                        <small>Date: ${video.date_added}</small>
                    </div>
                </div>
            </div>
        </div>
    `;
    if (prepend) {
        videoListContainer.insertAdjacentHTML('afterbegin', videoCard);
    } else {
        videoListContainer.insertAdjacentHTML('beforeend', videoCard);
    }
}


