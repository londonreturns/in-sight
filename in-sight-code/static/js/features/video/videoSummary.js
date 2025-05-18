import showToast from "../../modules/toast.js";

export function setupSummarySection(modalBody, videoId, contentType) {
    checkAndDisplaySummary(modalBody, videoId, contentType);

    const slider = modalBody.querySelector("#videoShortnerSensitivity");
    const sliderValue = modalBody.querySelector("#thresholdValue");
    const keyframeSlider = modalBody.querySelector("#keyframeThreshold");
    const keyframeSliderValue = modalBody.querySelector("#keyframeThresholdValue");
    const generateBtn = modalBody.querySelector("#generateSummaryBtn");

    if (slider) {
        slider.min = 0.1;
        if (parseFloat(slider.value) < 0.1) slider.value = 0.1;
        if (sliderValue) sliderValue.textContent = slider.value;
    }
    if (keyframeSlider) {
        keyframeSlider.min = 5;
        if (parseInt(keyframeSlider.value) < 5) keyframeSlider.value = 5;
        if (keyframeSliderValue) keyframeSliderValue.textContent = keyframeSlider.value;
    }

    if (slider && sliderValue) {
        slider.addEventListener("input", () => {
            sliderValue.textContent = slider.value;
        });
    }

    if (keyframeSlider && keyframeSliderValue) {
        keyframeSliderValue.textContent = keyframeSlider.value;
        keyframeSlider.addEventListener("input", () => {
            keyframeSliderValue.textContent = keyframeSlider.value;
        });
    }

    if (generateBtn) {

        const summaryTextContainer = modalBody.querySelector("#summaryTextContainer");
        summaryTextContainer.innerHTML = `<div class="d-flex justify-content-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>`;

        generateBtn.addEventListener("click", async () => {
            try {
                generateBtn.disabled = true;
                generateBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';

                showToast("Generating summary...", "processing", 999999);

                const threshold = parseFloat(slider?.value || "1.4");

                const response = await fetch(`/generateSummary/${videoId}`, {
                    method: "POST",
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({threshold})
                });

                const result = await response.json();

                if (!response.ok) {
                    showToast(result.error || "Error generating summary", "error");
                    return;
                }

                showToast("Summary generated successfully.", "success");
                displaySummary(modalBody, videoId, contentType);

                const summarizedVideoId = result.summarized_video_id;
                const keyframeThreshold = keyframeSlider ? keyframeSlider.value : 80;
                summaryTextContainer.innerHTML = `<div class="d-flex justify-content-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>`;
                try {
                    const textResp = await fetch(`/getSummarizedVideoText/${summarizedVideoId}?keyframe_threshold=${keyframeThreshold}`);
                    let textData = await textResp.json();
                    const timecodesResp = await fetch(`/getVideoTimecodes/${videoId}`);
                    const timecodesData = await timecodesResp.json();
                    textData = cleanSummaryObject(textData);
                    const timecodes = Array.isArray(timecodesData.timecodes) ? timecodesData.timecodes : null;
                    renderSummaryTabs(summaryTextContainer, textData, timecodes);
                } catch (err) {
                    summaryTextContainer.innerHTML = `<div class="alert alert-danger">Failed to load summary text.</div>`;
                }

            } catch (err) {
                console.error("Error generating summary:", err);
                showToast("An error occurred while generating summary", "error");
            } finally {
                generateBtn.disabled = false;
                generateBtn.textContent = "Generate Summary";
            }
        });
    }
}

function cleanSummaryObject(data) {
    const cleanFrameSummaries = data.frame_summaries.map(frame => {
        if (frame.raw) {
            let cleanedRaw = frame.raw.charAt(0).toUpperCase() + frame.raw.slice(1);
            cleanedRaw = cleanedRaw.replace(/\. ([a-z])/g, (match, char) => `. ${char.toUpperCase()}`);

            // Check if the last period exists before removing anything after it
            const lastDotIndex = cleanedRaw.lastIndexOf('.');
            if (lastDotIndex !== -1 && lastDotIndex < cleanedRaw.length - 1) {
                // Remove text after the last period, only if there's a period
                cleanedRaw = cleanedRaw.substring(0, lastDotIndex + 1);
            }
            return {raw: cleanedRaw};
        }
        return frame;
    });

    let cleanOverallSummaryRaw = "";
    if (data.overall_summary && data.overall_summary.raw) {
        cleanOverallSummaryRaw = data.overall_summary.raw.charAt(0).toUpperCase() + data.overall_summary.raw.slice(1);
        cleanOverallSummaryRaw = cleanOverallSummaryRaw.replace(/\. ([a-z])/g, (match, char) => `. ${char.toUpperCase()}`);

        // Check if the last period exists before removing anything after it
        const lastDotIndex = cleanOverallSummaryRaw.lastIndexOf('.');
        if (lastDotIndex !== -1 && lastDotIndex < cleanOverallSummaryRaw.length - 1) {
            // Remove text after the last period, only if there's a period
            cleanOverallSummaryRaw = cleanOverallSummaryRaw.substring(0, lastDotIndex + 1);
        }
    }

    return {
        frame_summaries: cleanFrameSummaries,
        overall_summary: {raw: cleanOverallSummaryRaw}
    };
}



function checkAndDisplaySummary(modalBody, videoId, contentType) {
    fetch(`/checkSummaryExists/${videoId}`)
        .then(res => res.json())
        .then(async data => {
            if (data.has_summary) {
                displaySummary(modalBody, videoId, contentType);

                let timecodes, textData;

                try {
                    let timecodesResp = await fetch(`/getVideoTimecodes/${videoId}`);
                    let timecodesData = await timecodesResp.json();
                    timecodes = Array.isArray(timecodesData.timecodes) ? timecodesData.timecodes : null;

                    let textResp = await fetch(`/getSummarizedTextFromDB/${videoId}`);
                    textData = await textResp.json();
                    textData = cleanSummaryObject(textData);
                } catch (err) {
                    showToast("Failed to load summary text.", "error");
                }

                let summaryTextContainer = modalBody.querySelector("#summaryTextContainer");
                renderSummaryTabs(summaryTextContainer, textData, timecodes);
            }
        })
        .catch(err => {
            console.error("Error checking summary existence:", err);
        });
}

function displaySummary(modalBody, videoId, contentType, summaryText = null) {
    const summarySection = modalBody.querySelector("#summarySection");
    summarySection.classList.remove("d-none");

    const summaryTextContainer = modalBody.querySelector("#summaryTextContainer");
    summaryTextContainer.innerHTML = `<div class="d-flex justify-content-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>`;

    const summarizedVideoContainer = modalBody.querySelector("#summarizedVideoContainer");
    summarizedVideoContainer.innerHTML = `
        <div class="ratio ratio-16x9">
            <video id="summarizedVideo" controls>
                <source src="/getSummarizedVideo/${videoId}" type="${contentType}">
                Your browser does not support the video tag.
            </video>
        </div>
        <div class="row">
            <div class="col-md-12 text-center">
                <div class="keyboard-controls-box">
                    <p>Keyboard Controls:</p>
                    <div class="btn-group">
                        <span class="btn btn-outline-black">J</span>
                        <span class="btn btn-outline-black" style="margin-left: 10px;">K</span>
                    </div>
                </div>
            </div>
        </div>
    `;

    setupKeyboardShortcuts(document.getElementById("summarizedVideo"));
}

function setupKeyboardShortcuts(videoEl) {
    if (!videoEl) return;

    if (window.videoKeyHandler) {
        document.removeEventListener("keydown", window.videoKeyHandler);
    }

    const handler = (e) => {
        const modal = document.getElementById("dynamicModal");
        if (!modal.classList.contains("show")) return;

        if (["j", "J", "k", "K"].includes(e.key)) {
            e.preventDefault();
        }

        if (e.key.toLowerCase() === "j") {
            videoEl.currentTime = 0;
            videoEl.pause();
        }

        if (e.key.toLowerCase() === "k") {
            videoEl.paused ? videoEl.play() : videoEl.pause();
        }
    };

    window.videoKeyHandler = handler;
    document.addEventListener("keydown", handler);
}


function renderSummaryTabs(container, summaryData, timecodes = null) {
    if (!summaryData) {
        container.innerHTML = `<p>No summary data available.</p>`;
        return;
    }

    const frameSummaries = Array.isArray(summaryData.frame_summaries) ? summaryData.frame_summaries : [];
    const overallSummary = summaryData.overall_summary;

    // Build tab headers
    let tabs = `<ul class="nav nav-tabs" id="summaryTabs" role="tablist">`;
    tabs += `<li class="nav-item" role="presentation">
        <button class="nav-link active" id="overall-tab" data-bs-toggle="tab" data-bs-target="#overall" type="button" role="tab" aria-controls="overall" aria-selected="true">Overall Summary</button>
    </li>`;
    frameSummaries.forEach((_, idx) => {
        let label = (timecodes && timecodes[idx]) ? timecodes[idx] : "";
        tabs += `<li class="nav-item" role="presentation">
            <button class="nav-link" id="frame${idx}-tab" data-bs-toggle="tab" data-bs-target="#frame${idx}" type="button" role="tab" aria-controls="frame${idx}" aria-selected="false">${label}</button>
        </li>`;
    });
    tabs += `</ul>`;

    // Build tab contents
    let tabContents = `<div class="tab-content mt-3" id="summaryTabsContent">`;
    tabContents += `<div class="tab-pane fade show active" id="overall" role="tabpanel" aria-labelledby="overall-tab">
        <pre style="white-space:pre-wrap;">${escapeHtml(overallSummary?.raw || "No summary available. Please try changing the threshold and retry.")}</pre>
    </div>`;
    frameSummaries.forEach((frame, idx) => {
        tabContents += `<div class="tab-pane fade" id="frame${idx}" role="tabpanel" aria-labelledby="frame${idx}-tab">
            <pre style="white-space:pre-wrap;">${escapeHtml(frame.raw || "No summary for this frame.")}</pre>
        </div>`;
    });
    tabContents += `</div>`;

    container.innerHTML = tabs + tabContents;
}

// Utility to escape HTML for safe rendering in <pre>
function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/[&<>"']/g, function (m) {
        switch (m) {
            case '&':
                return '&amp;';
            case '<':
                return '&lt;';
            case '>':
                return '&gt;';
            case '"':
                return '&quot;';
            case "'":
                return '&#39;';
            default:
                return m;
        }
    });
}
