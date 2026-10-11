
const form = document.getElementById("resumeForm");
const statusMessage = document.getElementById("status");
const results = document.getElementById("results");
const analyzeButton = document.getElementById("analyzeButton");

form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const resumeFile = document.getElementById("resume").files[0];

    const jobDescription = document
        .getElementById("jobDescription")
        .value.trim();

    if (!resumeFile || !jobDescription) {
        statusMessage.textContent =
            "Please upload a resume and enter a job description.";
        return;
    }

    if (
        resumeFile.type !== "application/pdf" &&
        !resumeFile.name.toLowerCase().endsWith(".pdf")
    ) {
        statusMessage.textContent = "Please upload a PDF file.";
        return;
    }

    if (resumeFile.size === 0 || resumeFile.size > 5 * 1024 * 1024) {
        statusMessage.textContent =
            "Choose a non-empty PDF smaller than 5 MB.";
        return;
    }

    const formData = new FormData();

    formData.append("resume", resumeFile);
    formData.append("job_description", jobDescription);

    analyzeButton.disabled = true;
    statusMessage.textContent = "Analysing your resume...";
    results.hidden = true;

    try {
        const response = await fetch(
            "http://127.0.0.1:8000/analyze",
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(
                data.detail || data.error || "Analysis failed."
            );
        }

        document.getElementById("score").textContent =
            data.match_percentage + "%";

        document.getElementById("resumeSkills").textContent =
            data.resume_skills.join(", ") || "No skills detected";

        document.getElementById("matchingSkills").textContent =
            data.matching_skills.join(", ") || "No matching skills";

        document.getElementById("missingSkills").textContent =
            data.missing_skills.join(", ") || "No missing skills";

        const suggestionList = document.getElementById("suggestions");
        suggestionList.replaceChildren();

        data.suggestions.forEach(function (suggestion) {
            const item = document.createElement("li");
            item.textContent = suggestion;
            suggestionList.appendChild(item);
        });

        results.hidden = false;
        statusMessage.textContent = "Analysis completed successfully!";

    } catch (error) {
        statusMessage.textContent =
            "Error: " + error.message +
            ". Check that the backend is running.";

    } finally {
        analyzeButton.disabled = false;
    }
});


