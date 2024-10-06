// Wait for the DOM to fully load
document.addEventListener('DOMContentLoaded', function () {
    // DOM Elements
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const messageDiv = document.getElementById('message');
    const buttonsDiv = document.getElementById('buttons');
    const chartContainer = document.getElementById('chart-container');
    const chartCanvas = document.getElementById('chart');

    // Variables
    let uploadedFilename = '';
    let chartUrls = [];
    let currentChart = null; // For Chart.js instance

    /**
     * Function to display messages to the user
     * @param {string} msg - The message to display
     * @param {string} type - The type of message ('success' or 'danger')
     */
    function displayMessage(msg, type) {
        messageDiv.innerHTML = `<div class="alert alert-${type}" role="alert">${msg}</div>`;
    }

    /**
     * Function to clear messages
     */
    function clearMessage() {
        messageDiv.innerHTML = '';
    }

    /**
     * Function to display the chart on the canvas
     * @param {string} chartUrl - The URL of the generated chart image
     */
    function displayChart(chartUrl) {
        // Clear the canvas
        const ctx = chartCanvas.getContext('2d');
        ctx.clearRect(0, 0, chartCanvas.width, chartCanvas.height);

        // Load the new chart image
        const img = new Image();
        img.src = chartUrl;
        img.onload = function () {
            ctx.drawImage(img, 0, 0, chartCanvas.width, chartCanvas.height);
        };
    }

    /**
     * Event Listener for File Upload Form Submission
     */
    uploadForm.addEventListener('submit', function (e) {
        e.preventDefault(); // Prevent default form submission

        const file = fileInput.files[0];
        if (!file) {
            alert('Please select a file to upload.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        // Initialize XMLHttpRequest
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/upload', true);

        // Update progress bar
        xhr.upload.onprogress = function (e) {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 100);
                progressBar.value = percentComplete;
                progressText.textContent = percentComplete + '%';
            }
        };

        // Show progress container
        xhr.onloadstart = function () {
            progressContainer.style.display = 'block';
            progressBar.value = 0;
            progressText.textContent = '0%';
            clearMessage();
            buttonsDiv.style.display = 'none';
            chartUrls = [];
            // Clear any existing charts
            displayChart('');
        };

        // Handle response
        xhr.onload = function () {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                if (response.status === 'success') {
                    displayMessage(response.message, 'success');
                    uploadedFilename = response.filename;
                    buttonsDiv.style.display = 'block';
                } else {
                    displayMessage(response.message, 'danger');
                }
            } else {
                displayMessage('Upload failed. Please try again.', 'danger');
            }
        };

        // Handle errors
        xhr.onerror = function () {
            displayMessage('An error occurred during the upload.', 'danger');
        };

        // Send the request
        xhr.send(formData);
    });

    /**
     * Function to generate a Bar Chart
     */
    window.generateBarChart = function() {
        if (!uploadedFilename) {
            alert('Please upload a file first.');
            return;
        }

        fetch('/generate_chart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type: 'bar', filename: uploadedFilename })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                displayMessage('Bar chart generated successfully.', 'success');
                displayChart(data.chart_url);
                chartUrls.push(data.chart_url);
            } else {
                displayMessage(data.message, 'danger');
            }
        })
        .catch(error => {
            console.error('Error generating bar chart:', error);
            displayMessage('An error occurred while generating the bar chart.', 'danger');
        });
    };

    /**
     * Function to generate a Pie Chart
     */
    window.generatePieChart = function() {
        if (!uploadedFilename) {
            alert('Please upload a file first.');
            return;
        }

        fetch('/generate_chart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type: 'pie', filename: uploadedFilename })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                displayMessage('Pie chart generated successfully.', 'success');
                displayChart(data.chart_url);
                chartUrls.push(data.chart_url);
            } else {
                displayMessage(data.message, 'danger');
            }
        })
        .catch(error => {
            console.error('Error generating pie chart:', error);
            displayMessage('An error occurred while generating the pie chart.', 'danger');
        });
    };

    /**
     * Function to generate a Line Chart
     */
    window.generateLineChart = function() {
        if (!uploadedFilename) {
            alert('Please upload a file first.');
            return;
        }

        fetch('/generate_chart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type: 'line', filename: uploadedFilename })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                displayMessage('Line graph generated successfully.', 'success');
                displayChart(data.chart_url);
                chartUrls.push(data.chart_url);
            } else {
                displayMessage(data.message, 'danger');
            }
        })
        .catch(error => {
            console.error('Error generating line graph:', error);
            displayMessage('An error occurred while generating the line graph.', 'danger');
        });
    };

    /**
     * Function to clear all charts and uploaded files
     */
    window.clearChart = function() {
        fetch('/clear', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    displayMessage(data.message, 'success');
                    chartUrls = [];
                    // Clear any displayed images on the canvas
                    const ctx = chartCanvas.getContext('2d');
                    ctx.clearRect(0, 0, chartCanvas.width, chartCanvas.height);
                    // Hide visualization buttons
                    buttonsDiv.style.display = 'none';
                    // Reset file input
                    fileInput.value = '';
                } else {
                    displayMessage(data.message, 'danger');
                }
            })
            .catch(error => {
                console.error('Error clearing files:', error);
                displayMessage('An error occurred while clearing files.', 'danger');
            });
    };

    /**
     * Function to download the report
     */
    window.downloadReport = function() {
        if (chartUrls.length === 0) {
            alert('Please generate at least one chart before downloading the report.');
            return;
        }

        fetch('/generate_report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ filename: uploadedFilename, charts: chartUrls })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.location.href = data.report_url;
            } else {
                displayMessage(data.message, 'danger');
            }
        })
        .catch(error => {
            console.error('Error generating report:', error);
            displayMessage('An error occurred while generating the report.', 'danger');
        });
    };
});
