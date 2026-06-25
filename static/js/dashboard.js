// Dashboard JavaScript

let currentScanType = 'camera';
let scanHistory = [];
let uploadedImage = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    initializeImageUpload();
});

function initializeDashboard() {
    // Scan option selection
    const scanOptions = document.querySelectorAll('.scan-option');
    scanOptions.forEach(option => {
        option.addEventListener('click', function() {
            scanOptions.forEach(opt => opt.classList.remove('active'));
            this.classList.add('active');
            currentScanType = this.dataset.type;
            
            // Show/hide appropriate forms
            const imageUpload = document.getElementById('imageUpload');
            const cameraFeed = document.getElementById('cameraFeed');
            const manualBarcode = document.getElementById('manualBarcode');
            const nutriScoreCalc = document.getElementById('nutriScoreCalc');
            
            if (currentScanType === 'upload') {
                imageUpload.style.display = 'block';
                cameraFeed.style.display = 'none';
                manualBarcode.style.display = 'none';
                if (nutriScoreCalc) nutriScoreCalc.style.display = 'none';
                stopLiveCamera();
            } else if (currentScanType === 'camera') {
                imageUpload.style.display = 'none';
                cameraFeed.style.display = 'block';
                manualBarcode.style.display = 'none';
                if (nutriScoreCalc) nutriScoreCalc.style.display = 'none';
                startLiveCamera();
            } else if (currentScanType === 'manual') {
                imageUpload.style.display = 'none';
                cameraFeed.style.display = 'none';
                manualBarcode.style.display = 'block';
                if (nutriScoreCalc) nutriScoreCalc.style.display = 'none';
                stopLiveCamera();
            } else if (currentScanType === 'nutricalc') {
                imageUpload.style.display = 'none';
                cameraFeed.style.display = 'none';
                manualBarcode.style.display = 'none';
                if (nutriScoreCalc) nutriScoreCalc.style.display = 'block';
                stopLiveCamera();
            }
        });
    });

    // Scan Upload Button
    const scanUploadBtn = document.getElementById('scanUploadBtn');
    if (scanUploadBtn) {
        scanUploadBtn.addEventListener('click', handleImageUploadScan);
    }
    
    // Submit Barcode Button
    const submitBarcodeBtn = document.getElementById('submitBarcodeBtn');
    if (submitBarcodeBtn) {
        submitBarcodeBtn.addEventListener('click', handleManualBarcodeScan);
    }

    // Run Nutri-Score Calculator Button
    const runCalcBtn = document.getElementById('runCalcBtn');
    if (runCalcBtn) {
        runCalcBtn.addEventListener('click', handleNutriScoreCalculation);
    }

    // Camera controls
    const stopCameraBtn = document.getElementById('stopCameraBtn');
    if (stopCameraBtn) {
        stopCameraBtn.addEventListener('click', stopLiveCamera);
    }

    // Load last scan if available
    loadLastScan();
    updateStats();
}

function initializeImageUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const imageFile = document.getElementById('imageFile');
    const browseBtn = document.getElementById('browseBtn');
    const previewArea = document.getElementById('previewArea');
    const previewImage = document.getElementById('previewImage');
    const removeImageBtn = document.getElementById('removeImageBtn');

    // Browse button click
    if (browseBtn) {
        browseBtn.addEventListener('click', () => imageFile.click());
    }

    // Upload area click
    if (uploadArea) {
        uploadArea.addEventListener('click', () => imageFile.click());
    }

    // File selection
    if (imageFile) {
        imageFile.addEventListener('change', handleFileSelect);
    }

    // Remove image
    if (removeImageBtn) {
        removeImageBtn.addEventListener('click', removeImage);
    }

    // Drag and drop
    if (uploadArea) {
        uploadArea.addEventListener('dragover', handleDragOver);
        uploadArea.addEventListener('dragleave', handleDragLeave);
        uploadArea.addEventListener('drop', handleDrop);
    }
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file && file.type.startsWith('image/')) {
        displayImage(file);
    } else {
        alert('Please select a valid image file.');
    }
}

function displayImage(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        uploadedImage = file;
        const previewImage = document.getElementById('previewImage');
        const previewArea = document.getElementById('previewArea');
        
        previewImage.src = e.target.result;
        previewArea.style.display = 'block';
    };
    reader.readAsDataURL(file);
}

function removeImage() {
    uploadedImage = null;
    const imageFile = document.getElementById('imageFile');
    const previewArea = document.getElementById('previewArea');
    
    imageFile.value = '';
    previewArea.style.display = 'none';
}

function handleDragOver(event) {
    event.preventDefault();
    event.currentTarget.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('dragover');
}

function handleDrop(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('dragover');
    
    const files = event.dataTransfer.files;
    if (files.length > 0 && files[0].type.startsWith('image/')) {
        displayImage(files[0]);
    } else {
        alert('Please drop a valid image file.');
    }
}

async function handleImageUploadScan() {
    const scanUploadBtn = document.getElementById('scanUploadBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    if (!uploadedImage) {
        alert('Please select an image to upload');
        return;
    }
    
    loadingOverlay.style.display = 'flex';
    scanUploadBtn.disabled = true;
    
    try {
        const formData = new FormData();
        formData.append('image', uploadedImage);
        formData.append('type', 'upload');
        
        const response = await fetch('/scan', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            const displayResult = result.result;
            displayResult.ai_analysis = result.ai_analysis;
            displayResult.open_food_facts = result.open_food_facts;
            
            // Add to in-memory history
            const newScan = {
                dashboard: {
                    id: result.scan_id,
                    'Product Name': displayResult['Product Name'],
                    'Brand': displayResult['Brand'],
                    'Veg Status': displayResult['Veg Status'],
                    'Safety Color': displayResult['Safety Color'],
                    'Safety Score': displayResult['Safety Score'],
                    'Health Warnings': displayResult['Health Warnings'] || [],
                    image_url: result.open_food_facts ? result.open_food_facts.image_url : null,
                    nutriscore: result.open_food_facts ? result.open_food_facts.nutriscore : null
                }
            };
            scanHistory.unshift(newScan);
            
            showScanResults(displayResult, result.scan_id);
            updateRecentScans();
            updateStats();
            removeImage();
        } else {
            alert('Scan failed: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Scan error:', error);
        alert('An error occurred during scanning. Please try again.');
    } finally {
        loadingOverlay.style.display = 'none';
        scanUploadBtn.disabled = false;
    }
}

async function handleManualBarcodeScan() {
    const submitBarcodeBtn = document.getElementById('submitBarcodeBtn');
    const barcodeInput = document.getElementById('barcodeInput');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    const barcode = barcodeInput.value.trim();
    if (!barcode) {
        alert('Please enter a barcode');
        return;
    }
    
    loadingOverlay.style.display = 'flex';
    submitBarcodeBtn.disabled = true;
    
    try {
        const response = await fetch('/scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                type: 'barcode',
                barcode: barcode
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            const displayResult = result.result;
            displayResult.ai_analysis = result.ai_analysis;
            displayResult.open_food_facts = result.open_food_facts;
            
            // Add to in-memory history
            const newScan = {
                dashboard: {
                    id: result.scan_id,
                    'Product Name': displayResult['Product Name'],
                    'Brand': displayResult['Brand'],
                    'Veg Status': displayResult['Veg Status'],
                    'Safety Color': displayResult['Safety Color'],
                    'Safety Score': displayResult['Safety Score'],
                    'Health Warnings': displayResult['Health Warnings'] || [],
                    image_url: result.open_food_facts ? result.open_food_facts.image_url : null,
                    nutriscore: result.open_food_facts ? result.open_food_facts.nutriscore : null
                }
            };
            scanHistory.unshift(newScan);
            
            showScanResults(displayResult, result.scan_id);
            updateRecentScans();
            updateStats();
            barcodeInput.value = '';
        } else {
            alert('Product lookup failed: ' + (result.error || 'Product not found in Open Food Facts.'));
        }
    } catch (error) {
        console.error('Barcode lookup error:', error);
        alert('An error occurred. Please check your connection.');
    } finally {
        loadingOverlay.style.display = 'none';
        submitBarcodeBtn.disabled = false;
    }
}

function loadLastScan() {
    fetch('/api/history')
        .then(response => response.json())
        .then(data => {
            if (data && data.length > 0) {
                scanHistory = data.map(scan => ({
                    dashboard: {
                        id: scan.id,
                        'Product Name': scan.product_name,
                        'Brand': scan.brand,
                        'Veg Status': scan.veg_status,
                        'Safety Color': scan.safety_color,
                        'Safety Score': scan.safety_score,
                        'Health Warnings': scan.health_warnings || [],
                        image_url: scan.image_url,
                        nutriscore: scan.nutriscore
                    }
                }));
                updateRecentScans();
                updateStats();
            }
        })
        .catch(error => console.error('Error loading scan history:', error));
}

function updateRecentScans() {
    const recentScansContainer = document.getElementById('recentScans');
    
    if (scanHistory.length === 0) {
        recentScansContainer.innerHTML = '<p class="empty-state">No scans yet. Start scanning to see results here.</p>';
        return;
    }
    
    recentScansContainer.innerHTML = scanHistory.slice(0, 5).map(scan => {
        const dashboard = scan.dashboard;
        const safetyColor = dashboard['Safety Color'].toLowerCase();
        
        return `
            <div class="scan-item" onclick="showScanDetails(${JSON.stringify(scan).replace(/"/g, '&quot;')})">
                <div class="scan-item-info">
                    <div class="scan-item-name">${escapeHtml(dashboard['Product Name'])}</div>
                    <div class="scan-item-meta">${escapeHtml(dashboard['Brand'])} • ${escapeHtml(dashboard['Veg Status'])}</div>
                </div>
                <div class="scan-item-status">
                    <span class="badge badge-${safetyColor}">${escapeHtml(dashboard['Safety Color'])}</span>
                    <span style="color: var(--gray-500); font-size: 14px;">${dashboard['Safety Score']}/100</span>
                </div>
            </div>
        `;
    }).join('');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function updateStats() {
    // Update total scans
    document.getElementById('totalScans').textContent = scanHistory.length;
    
    // Calculate safe products (GREEN rating)
    const safeProducts = scanHistory.filter(scan => 
        scan.dashboard['Safety Color'] === 'GREEN'
    ).length;
    document.getElementById('safeProducts').textContent = safeProducts;
    
    // Calculate total warnings
    const totalWarnings = scanHistory.reduce((sum, scan) => 
        sum + scan.dashboard['Health Warnings'].length, 0
    );
    document.getElementById('warnings').textContent = totalWarnings;
}

function closeResultsModal() {
    const modal = document.getElementById('resultsModal');
    modal.style.display = 'none';
}

// Store current scan results for report generation
let currentScanResult = null;
let currentScanId = null;

function showScanResults(result, scanId) {
    currentScanResult = result; // Store for report generation
    currentScanId = scanId; // Store scan ID for PDF download
    
    const modal = document.getElementById('resultsModal');
    const content = document.getElementById('resultsContent');
    const downloadPdfBtn = document.getElementById('downloadPdfBtn');
    
    // Show PDF button for normal scans
    if (downloadPdfBtn) {
        downloadPdfBtn.style.display = 'inline-flex';
    }
    
    // Generate safety badge class
    const safetyColor = result['Safety Color'].toLowerCase();
    const safetyClass = `safety-${safetyColor}`;
    
    // Generate health warnings HTML
    const warningsHtml = result['Health Warnings'].length > 0 ? 
        result['Health Warnings'].map(warning => `
            <div class="warning-item">
                <div class="warning-ingredient">${escapeHtml(warning.ingredient)}</div>
                <div class="warning-conditions">${warning.conditions.map(condition => escapeHtml(condition)).join(', ')}</div>
            </div>
        `).join('') : 
        '<p style="color: #059669; font-weight: 500;">✓ No health warnings detected</p>';
    
    // Generate ingredients list
    const ingredientsHtml = result['Ingredients'].map(ingredient => 
        `<span class="ingredient-tag">${escapeHtml(ingredient)}</span>`
    ).join('');
    
    // Check if AI analysis is available
    const aiAnalysis = result.ai_analysis || null;
    const aiSummaryHtml = aiAnalysis ? `
        <div class="result-section">
            <h3>🤖 Gemini AI Personal Health Assessment</h3>
            <div class="ai-summary">
                <div class="result-row">
                    <span class="result-label">Product Category:</span>
                    <span class="result-value">${escapeHtml(aiAnalysis.product_category || 'N/A')}</span>
                </div>
                <div class="result-row">
                    <span class="result-label">Dietary Suitability:</span>
                    <span class="result-value">
                        ${aiAnalysis.dietary_suitability ? 
                            `${aiAnalysis.dietary_suitability.vegetarian ? '🌱 Vegetarian ' : ''}${aiAnalysis.dietary_suitability.vegan ? '🌿 Vegan ' : ''}${aiAnalysis.dietary_suitability.gluten_free ? '🌾 Gluten-Free ' : ''}${aiAnalysis.dietary_suitability.dairy_free ? '🥛 Dairy-Free ' : ''}` 
                            : 'N/A'}
                    </span>
                </div>
                <div class="result-row">
                    <span class="result-label">Health Benefits:</span>
                    <span class="result-value">${aiAnalysis.health_benefits && aiAnalysis.health_benefits.length > 0 ? aiAnalysis.health_benefits.map(b => escapeHtml(b)).join(', ') : 'Standard nutritional value'}</span>
                </div>
                <div class="result-row" style="flex-direction: column; align-items: flex-start; gap: 4px;">
                    <span class="result-label">Health Impact:</span>
                    <span class="result-value" style="font-style: italic; color: var(--gray-600);">${escapeHtml(aiAnalysis.health_impact || 'N/A')}</span>
                </div>
            </div>
        </div>
        
        <div class="result-section">
            <h3>🎯 Expert Recommendations</h3>
            <div class="ai-summary">
                <p><strong>Usage:</strong> ${escapeHtml(aiAnalysis.usage_recommendations || 'Use according to package instructions')}</p>
                <p><strong>Storage:</strong> ${escapeHtml(aiAnalysis.storage_recommendations || 'Store in cool, dry place')}</p>
                <p><strong>Guidelines:</strong> ${escapeHtml(aiAnalysis.consumption_guidelines || 'Consume in moderation')}</p>
            </div>
        </div>
        
        <div class="result-section">
            <h3>📊 Expert Summary</h3>
            <div class="ai-summary">
                <p><em>${escapeHtml(aiAnalysis.expert_summary || 'Product analysis completed successfully.')}</em></p>
            </div>
        </div>
    ` : '';
    
    // Generate Open Food Facts premium assets HTML
    let offHtml = '';
    const openFoodFacts = result.open_food_facts || null;
    
    // Generate Nutri-Score calculated points breakdown if available
    let calcBreakdownHtml = '';
    if (openFoodFacts && openFoodFacts.nutriscore_calculated) {
        const calc = openFoodFacts.nutriscore_calculated;
        const bd = calc.breakdown || {};
        
        calcBreakdownHtml = `
            <div class="result-section" style="background: var(--gray-50); border: 1px solid var(--gray-200); border-radius: 10px; padding: 15px; margin-bottom: 20px;">
                <h4 style="font-size: 14px; font-weight: 600; margin-top: 0; margin-bottom: 10px; color: var(--gray-700); display: flex; justify-content: space-between; align-items: center;">
                    <span>📊 Dynamic Nutri-Score Points Breakdown</span>
                    <span style="font-size: 12px; color: var(--primary-blue); font-weight: 700;">Score: ${calc.final_score} (${calc.letter})</span>
                </h4>
                
                <div style="display: flex; gap: 8px; margin-bottom: 10px; font-size: 12px; text-align: center;">
                    <div style="flex: 1; background: #fff5f5; border-radius: 6px; padding: 6px; border: 1px solid #fee2e2;">
                        <span style="color: #991b1b; font-weight: 700;">Negative (A): +${calc.negative_points}</span>
                    </div>
                    <div style="flex: 1; background: #f0fdf4; border-radius: 6px; padding: 6px; border: 1px solid #d1fae5;">
                        <span style="color: #065f46; font-weight: 700;">Positive (C): -${calc.positive_points}</span>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; font-size: 12px;">
                    <div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                            <span>Energy:</span>
                            <strong style="color: #c53030;">+${bd.energy || 0} pts</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                            <span>Saturated Fat:</span>
                            <strong style="color: #c53030;">+${bd.sat_fat || 0} pts</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                            <span>Sugars:</span>
                            <strong style="color: #c53030;">+${bd.sugars || 0} pts</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                            <span>Salt:</span>
                            <strong style="color: #c53030;">+${bd.salt || 0} pts</strong>
                        </div>
                    </div>
                    <div style="border-left: 1px dashed var(--gray-300); padding-left: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                            <span>Fiber:</span>
                            <strong style="color: #15803d;">-${bd.fiber || 0} pts</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                            <span>Protein:</span>
                            <strong style="color: #15803d;">-${bd.protein || 0} pts</strong>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                            <span>Fruits/Veg/Nuts:</span>
                            <strong style="color: #15803d;">-${bd.fruit_veg || 0} pts</strong>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    if (openFoodFacts && openFoodFacts.barcode) {
        // Image thumbnail
        const imgHtml = openFoodFacts.image_url ? 
            `<div class="product-image-container" style="text-align: center; margin-bottom: 20px;">
                <img src="${openFoodFacts.image_url}" alt="Product Image" class="product-thumb" style="max-height: 180px; border-radius: 12px; box-shadow: var(--shadow-md);">
             </div>` : 
            `<div class="product-image-container placeholder-gradient" style="text-align: center; margin-bottom: 20px; padding: 30px; background: linear-gradient(135deg, var(--gray-100), var(--gray-200)); border-radius: 12px; color: var(--gray-400); font-weight: 600;">
                <span>No Product Photo</span>
             </div>`;
             
        // Badges for Nutriscore, Nova, Ecoscore
        const nutriscore = openFoodFacts.nutriscore ? openFoodFacts.nutriscore.toUpperCase() : 'N/A';
        const nova = openFoodFacts.nova_group || 'N/A';
        const ecoscore = openFoodFacts.ecoscore ? openFoodFacts.ecoscore.toUpperCase() : 'N/A';
        
        const nutriClass = `nutri-${nutriscore.toLowerCase()}`;
        const novaClass = `nova-${nova}`;
        const ecoClass = `eco-${ecoscore.toLowerCase()}`;
        
        // Nutriments Table
        const nutriments = openFoodFacts.nutriments || {};
        const calories = nutriments['energy-kcal_100g'] !== undefined ? Math.round(nutriments['energy-kcal_100g']) : 
                         (nutriments['energy_100g'] !== undefined ? Math.round(nutriments['energy_100g'] / 4.184) : 'N/A');
        const fat = nutriments['fat_100g'] !== undefined ? nutriments['fat_100g'].toFixed(1) : 'N/A';
        const satFat = nutriments['saturated-fat_100g'] !== undefined ? nutriments['saturated-fat_100g'].toFixed(1) : 'N/A';
        const carbs = nutriments['carbohydrates_100g'] !== undefined ? nutriments['carbohydrates_100g'].toFixed(1) : 'N/A';
        const sugars = nutriments['sugars_100g'] !== undefined ? nutriments['sugars_100g'].toFixed(1) : 'N/A';
        const proteins = nutriments['proteins_100g'] !== undefined ? nutriments['proteins_100g'].toFixed(1) : 'N/A';
        const salt = nutriments['salt_100g'] !== undefined ? nutriments['salt_100g'].toFixed(2) : 
                     (nutriments['sodium_100g'] !== undefined ? (nutriments['sodium_100g'] * 2.5).toFixed(2) : 'N/A');

        offHtml = `
            <div class="result-section product-header-section" style="display: flex; flex-direction: column; align-items: center; border-bottom: 1px solid var(--gray-200); padding-bottom: 20px; margin-bottom: 20px;">
                ${imgHtml}
                <div class="product-header-details" style="text-align: center;">
                    <span class="barcode-badge" style="background: var(--gray-100); color: var(--gray-600); padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; letter-spacing: 0.5px; border: 1px solid var(--gray-200);">EAN: ${openFoodFacts.barcode}</span>
                    <h2 class="product-title" style="font-size: 22px; font-weight: 700; margin-top: 10px; color: var(--gray-900);">${escapeHtml(result['Product Name'])}</h2>
                    <h4 class="product-brand" style="font-size: 14px; font-weight: 500; color: var(--gray-500); margin-top: 2px;">by ${escapeHtml(result['Brand'])}</h4>
                </div>
            </div>
            
            <div class="result-section">
                <h3>Global Food Database Indicators</h3>
                <div class="indicators-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px;">
                    <div class="indicator-card" style="background: var(--gray-50); border: 1px solid var(--gray-200); border-radius: 10px; padding: 12px; text-align: center;">
                        <div class="indicator-label" style="font-size: 11px; font-weight: 600; color: var(--gray-500); margin-bottom: 8px; text-transform: uppercase;">Nutri-Score</div>
                        <div class="score-badge ${nutriClass}" style="display: inline-block; width: 40px; height: 40px; line-height: 40px; border-radius: 50%; font-size: 20px; font-weight: 800; text-align: center; color: white;">${nutriscore}</div>
                    </div>
                    <div class="indicator-card" style="background: var(--gray-50); border: 1px solid var(--gray-200); border-radius: 10px; padding: 12px; text-align: center;">
                        <div class="indicator-label" style="font-size: 11px; font-weight: 600; color: var(--gray-500); margin-bottom: 8px; text-transform: uppercase;">NOVA Group</div>
                        <div class="score-badge ${novaClass}" style="display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; color: white;">Group ${nova}</div>
                    </div>
                    <div class="indicator-card" style="background: var(--gray-50); border: 1px solid var(--gray-200); border-radius: 10px; padding: 12px; text-align: center;">
                        <div class="indicator-label" style="font-size: 11px; font-weight: 600; color: var(--gray-500); margin-bottom: 8px; text-transform: uppercase;">Eco-Score</div>
                        <div class="score-badge ${ecoClass}" style="display: inline-block; width: 40px; height: 40px; line-height: 40px; border-radius: 50%; font-size: 20px; font-weight: 800; text-align: center; color: white;">${ecoscore}</div>
                    </div>
                </div>
            </div>
            
            <div class="result-section">
                <h3>Nutrition Facts (per 100g)</h3>
                <div class="nutrition-table-wrapper" style="border: 1px solid var(--gray-200); border-radius: 10px; overflow: hidden; margin-bottom: 20px;">
                    <table class="nutrition-table" style="width: 100%; border-collapse: collapse; text-align: left; font-size: 14px;">
                        <thead>
                            <tr style="background: var(--gray-50); border-bottom: 1px solid var(--gray-200);">
                                <th style="padding: 10px 15px; font-weight: 600; color: var(--gray-700);">Nutrient</th>
                                <th style="padding: 10px 15px; font-weight: 600; color: var(--gray-700); text-align: right;">Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="border-bottom: 1px solid var(--gray-100);"><td style="padding: 8px 15px;">🔥 Energy (Calories)</td><td style="padding: 8px 15px; text-align: right; font-weight: 700; color: var(--gray-800);">${calories} kcal</td></tr>
                            <tr style="border-bottom: 1px solid var(--gray-100);"><td style="padding: 8px 15px;">🧈 Fat</td><td style="padding: 8px 15px; text-align: right; font-weight: 700; color: var(--gray-800);">${fat} g</td></tr>
                            <tr style="border-bottom: 1px solid var(--gray-100);"><td style="padding: 8px 15px; padding-left: 30px; color: var(--gray-500);">↳ Saturated Fat</td><td style="padding: 8px 15px; text-align: right; font-weight: 600; color: var(--gray-600);">${satFat} g</td></tr>
                            <tr style="border-bottom: 1px solid var(--gray-100);"><td style="padding: 8px 15px;">🍞 Carbohydrates</td><td style="padding: 8px 15px; text-align: right; font-weight: 700; color: var(--gray-800);">${carbs} g</td></tr>
                            <tr style="border-bottom: 1px solid var(--gray-100);"><td style="padding: 8px 15px; padding-left: 30px; color: var(--gray-500);">↳ Sugars</td><td style="padding: 8px 15px; text-align: right; font-weight: 600; color: var(--gray-600);">${sugars} g</td></tr>
                            <tr style="border-bottom: 1px solid var(--gray-100);"><td style="padding: 8px 15px;">💪 Proteins</td><td style="padding: 8px 15px; text-align: right; font-weight: 700; color: var(--gray-800);">${proteins} g</td></tr>
                            <tr><td style="padding: 8px 15px;">🧂 Salt</td><td style="padding: 8px 15px; text-align: right; font-weight: 700; color: var(--gray-800);">${salt} g</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
    
    // Build fallback standard header if no OFF EAN was scanned
    const standardHeaderHtml = !offHtml ? `
        <div class="result-section">
            <h3>Product Information</h3>
            <div class="result-info">
                <div class="result-row">
                    <span class="result-label">Product Name:</span>
                    <span class="result-value">${escapeHtml(result['Product Name'])}</span>
                </div>
                <div class="result-row">
                    <span class="result-label">Brand:</span>
                    <span class="result-value">${escapeHtml(result['Brand'])}</span>
                </div>
                <div class="result-row">
                    <span class="result-label">Vegetarian Status:</span>
                    <span class="result-value">${escapeHtml(result['Veg Status'])}</span>
                </div>
            </div>
        </div>
    ` : '';

    content.innerHTML = `
        ${offHtml}
        ${calcBreakdownHtml}
        ${standardHeaderHtml}
        
        <div class="result-section">
            <h3>Safety Assessment</h3>
            <div class="result-info">
                <div class="result-row">
                    <span class="result-label">Safety Rating:</span>
                    <span class="safety-badge ${safetyClass}">${escapeHtml(result['Safety Color'])}</span>
                </div>
                <div class="result-row">
                    <span class="result-label">Safety Score:</span>
                    <span class="result-value">${result['Safety Score']}/100</span>
                </div>
            </div>
        </div>
        
        <div class="result-section">
            <h3>Ingredients (${result['Ingredients'].length})</h3>
            <div class="ingredient-list">
                ${ingredientsHtml}
            </div>
        </div>
        
        <div class="result-section">
            <h3>Health Warnings</h3>
            ${warningsHtml}
        </div>
        
        ${aiSummaryHtml}
    `;
    
    modal.style.display = 'flex';
}

function generateReport() {
    if (!currentScanId) {
        alert('No scan results available for report generation');
        return;
    }
    
    // Download PDF directly
    window.location.href = `/download/pdf/${currentScanId}`;
}

function generateComprehensiveReport(result) {
    const timestamp = new Date().toLocaleString();
    const safetyColor = result['Safety Color'].toLowerCase();
    
    // Get AI analysis if available
    const aiAnalysis = result.ai_analysis || null;
    
    return `
FOOD PRODUCT ANALYSIS REPORT
============================

Generated: ${timestamp}

PRODUCT INFORMATION
------------------
Product Name: ${result['Product Name']}
Brand: ${result['Brand']}
Vegetarian Status: ${result['Veg Status']}

SAFETY ASSESSMENT
-----------------
Safety Rating: ${result['Safety Color']}
Safety Score: ${result['Safety Score']}/100

INGREDIENTS ANALYSIS
--------------------
Total Ingredients: ${result['Ingredients'].length}

${result['Ingredients'].map((ing, index) => `${index + 1}. ${ing}`).join('\n')}

HEALTH WARNINGS
---------------
${result['Health Warnings'].length > 0 ? 
    result['Health Warnings'].map((warning, index) => `
${index + 1}. ${warning.ingredient}
   Conditions: ${warning.conditions.join(', ')}
`).join('\n') : 
    'No health warnings detected.'
}

${aiAnalysis ? `
🤖 GEMINI AI ANALYSIS
======================

PRODUCT CATEGORY: ${aiAnalysis.product_category || 'N/A'}

HEALTH IMPACT: ${aiAnalysis.health_impact || 'N/A'}

DIETARY INFORMATION:
- Vegetarian: ${aiAnalysis.dietary_suitability?.vegetarian ? 'Yes' : 'No'}
- Vegan: ${aiAnalysis.dietary_suitability?.vegan ? 'Yes' : 'No'}
- Gluten-Free: ${aiAnalysis.dietary_suitability?.gluten_free ? 'Yes' : 'No'}
- Dairy-Free: ${aiAnalysis.dietary_suitability?.dairy_free ? 'Yes' : 'No'}

ALLEGENS DETECTED:
${aiAnalysis.allergens && aiAnalysis.allergens.length > 0 ? 
    aiAnalysis.allergens.map((allergen, index) => `${index + 1}. ${allergen}`).join('\n') : 
    'No allergens detected.'
}

HEALTH BENEFITS:
${aiAnalysis.health_benefits && aiAnalysis.health_benefits.length > 0 ? 
    aiAnalysis.health_benefits.map((benefit, index) => `${index + 1}. ${benefit}`).join('\n') : 
    'Standard nutritional value.'
}

EXPERT RECOMMENDATIONS:
----------------------
Usage: ${aiAnalysis.usage_recommendations || 'Use according to package instructions'}
Storage: ${aiAnalysis.storage_recommendations || 'Store in cool, dry place'}
Guidelines: ${aiAnalysis.consumption_guidelines || 'Consume in moderation'}

EXPERT SUMMARY:
---------------
${aiAnalysis.expert_summary || 'Product analysis completed successfully.'}
` : ''}

AI PRODUCT SUMMARY
------------------
Product Analysis: ${result['Product Name']} by ${result['Brand']} is classified as ${result['Veg Status']} with a safety rating of ${result['Safety Color']} (${result['Safety Score']}/100).

Key Findings: This product contains ${result['Ingredients'].length} ingredients. ${result['Health Warnings'].length > 0 ? `There are ${result['Health Warnings'].length} health warnings to be aware of, particularly regarding: ${result['Health Warnings'].slice(0, 2).map(w => w.ingredient).join(' and ')}.` : 'No significant health warnings were detected.'}

Recommendation: ${result['Safety Score'] >= 80 ? 'This product appears to be safe for consumption with minimal health concerns.' : result['Safety Score'] >= 60 ? 'This product is moderately safe but should be consumed in moderation due to some ingredients.' : 'This product has several health concerns. Consider alternatives or consume sparingly.'}

DETAILED ANALYSIS
----------------
Safety Classification: ${safetyColor}
Risk Level: ${safetyColor === 'green' ? 'Low' : safetyColor === 'yellow' ? 'Moderate' : safetyColor === 'orange' ? 'High' : 'Very High'}

${result['Health Warnings'].length > 0 ? `
CRITICAL INGREDIENTS TO WATCH:
${result['Health Warnings'].map(w => `- ${w.ingredient}: ${w.conditions.join(', ')}`).join('\n')}
` : ''}

RECOMMENDATIONS
---------------
1. Always check ingredient labels before consumption
2. Consult with healthcare provider for specific dietary concerns
3. Consider alternative products if you have sensitivities to listed ingredients
4. Store product according to manufacturer guidelines
5. Monitor for any allergic reactions when trying new products

${aiAnalysis ? `
AI-POWERED INSIGHTS:
--------------------
This analysis was enhanced with Google's Gemini AI model for comprehensive product understanding and personalized recommendations.
` : ''}

DISCLAIMER
----------
This report is generated by AI analysis and should not replace professional medical advice. 
Always consult with healthcare professionals for specific dietary concerns and medical conditions.

============================
End of Report
    `.trim();
}

function downloadReport(reportContent, result) {
    // Create blob
    const blob = new Blob([reportContent], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    
    // Create download link
    const a = document.createElement('a');
    a.href = url;
    a.download = `${result['Product Name']}_Analysis_Report_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

async function showScanDetails(scan) {
    const scanId = scan.dashboard.id;
    if (scanId) {
        try {
            // Show loading overlay
            const loadingOverlay = document.getElementById('loadingOverlay');
            if (loadingOverlay) loadingOverlay.style.display = 'flex';
            
            const response = await fetch(`/api/scan/${scanId}`);
            const data = await response.json();
            
            if (data.success) {
                const result = data.result.dashboard;
                result.ai_analysis = data.result.ai_analysis;
                result.open_food_facts = data.result.open_food_facts;
                showScanResults(result, scanId);
                return;
            }
        } catch (e) {
            console.error("Error fetching historical scan details:", e);
        } finally {
            const loadingOverlay = document.getElementById('loadingOverlay');
            if (loadingOverlay) loadingOverlay.style.display = 'none';
        }
    }
    
    // Fallback if not cached or fetch fails
    showScanResults(scan.dashboard);
}

async function handleNutriScoreCalculation() {
    const runCalcBtn = document.getElementById('runCalcBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    // Get all values from inputs
    const category = document.getElementById('calcCategory').value;
    const energyUnit = document.getElementById('calcEnergyUnit').value;
    const energy = parseFloat(document.getElementById('calcEnergy').value) || 0;
    const satFat = parseFloat(document.getElementById('calcSatFat').value) || 0;
    const sugars = parseFloat(document.getElementById('calcSugars').value) || 0;
    const salt = parseFloat(document.getElementById('calcSalt').value) || 0;
    const fiber = parseFloat(document.getElementById('calcFiber').value) || 0;
    const protein = parseFloat(document.getElementById('calcProtein').value) || 0;
    const fruitVeg = parseFloat(document.getElementById('calcFruitVeg').value) || 0;
    
    if (loadingOverlay) loadingOverlay.style.display = 'flex';
    if (runCalcBtn) runCalcBtn.disabled = true;
    
    try {
        const payload = {
            category: category,
            is_beverage: category === 'beverage',
            is_cheese: category === 'cheese',
            is_fat_oil: category === 'fats_oils_nuts',
            energy_kj: energy,
            energy_unit: energyUnit,
            sat_fat: satFat,
            sugars: sugars,
            salt: salt,
            fiber: fiber,
            protein: protein,
            fruit_veg_percentage: fruitVeg
        };
        
        const response = await fetch('/api/nutri-score/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showCalculatorResults(result.result, payload);
        } else {
            alert('Calculation failed: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Calculator error:', error);
        alert('An error occurred. Please try again.');
    } finally {
        if (loadingOverlay) loadingOverlay.style.display = 'none';
        if (runCalcBtn) runCalcBtn.disabled = false;
    }
}

function showCalculatorResults(calcResult, inputs) {
    const modal = document.getElementById('resultsModal');
    const content = document.getElementById('resultsContent');
    const downloadPdfBtn = document.getElementById('downloadPdfBtn');
    
    // Hide PDF button for manual calculations
    if (downloadPdfBtn) {
        downloadPdfBtn.style.display = 'none';
    }
    
    const letter = calcResult.letter.toUpperCase();
    const nutriClass = `nutri-${letter.toLowerCase()}`;
    const score = calcResult.final_score;
    const breakdown = calcResult.breakdown || {};
    
    // Map category value for display
    let categoryText = "General Foods";
    if (inputs.category === 'beverage') categoryText = "Beverages";
    else if (inputs.category === 'cheese') categoryText = "Cheese";
    else if (inputs.category === 'red_meat') categoryText = "Red Meat";
    else if (inputs.category === 'fats_oils_nuts') categoryText = "Fats, Oils & Nuts";
    
    // Construct HTML for points breakdown
    const pointsHtml = `
        <div class="result-section" style="text-align: center; border-bottom: 1px solid var(--gray-200); padding-bottom: 20px; margin-bottom: 20px;">
            <div class="score-badge ${nutriClass}" style="display: inline-block; width: 80px; height: 80px; line-height: 80px; border-radius: 50%; font-size: 42px; font-weight: 800; text-align: center; color: white; margin-bottom: 12px; box-shadow: var(--shadow-md);">
                ${letter}
            </div>
            <h2 style="font-size: 20px; font-weight: 700; color: var(--gray-900);">Nutri-Score Calculated: ${letter}</h2>
            <p style="font-size: 14px; color: var(--gray-500); margin-top: 4px;">FSA-NPS Final Score: <span style="font-weight: 700; color: var(--gray-800); font-size: 16px;">${score}</span></p>
            <span class="badge badge-blue" style="margin-top: 8px;">${categoryText} Category</span>
        </div>
        
        <div class="result-section">
            <h3 style="font-size: 15px; font-weight: 600; color: var(--gray-700); margin-bottom: 12px; border-bottom: 1px solid var(--gray-100); padding-bottom: 6px;">Points Summary</h3>
            <div style="display: flex; gap: 16px; margin-bottom: 20px;">
                <div style="flex: 1; background: #fee2e2; border-radius: 8px; padding: 12px; text-align: center;">
                    <div style="font-size: 11px; font-weight: 700; color: #991b1b; text-transform: uppercase;">Negative Points (A)</div>
                    <div style="font-size: 24px; font-weight: 800; color: #991b1b; margin-top: 4px;">+${calcResult.negative_points}</div>
                    <div style="font-size: 11px; color: #b91c1c; margin-top: 2px;">Energy, Sat Fat, Sugar, Salt</div>
                </div>
                <div style="flex: 1; background: #d1fae5; border-radius: 8px; padding: 12px; text-align: center;">
                    <div style="font-size: 11px; font-weight: 700; color: #065f46; text-transform: uppercase;">Positive Points (C)</div>
                    <div style="font-size: 24px; font-weight: 800; color: #065f46; margin-top: 4px;">-${calcResult.positive_points}</div>
                    <div style="font-size: 11px; color: #047857; margin-top: 2px;">Fiber, Protein, Fruits/Veg</div>
                </div>
            </div>
        </div>
        
        <div class="result-section">
            <h3 style="font-size: 15px; font-weight: 600; color: var(--gray-700); margin-bottom: 12px; border-bottom: 1px solid var(--gray-100); padding-bottom: 6px;">Nutrient Breakdown (Points Contribution)</h3>
            <div class="nutrition-table-wrapper" style="border: 1px solid var(--gray-200); border-radius: 10px; overflow: hidden;">
                <table class="nutrition-table" style="width: 100%; border-collapse: collapse; text-align: left; font-size: 14px;">
                    <thead>
                        <tr style="background: var(--gray-50); border-bottom: 1px solid var(--gray-200);">
                            <th style="padding: 10px 15px; font-weight: 600; color: var(--gray-700);">Nutrient Fact</th>
                            <th style="padding: 10px 15px; font-weight: 600; color: var(--gray-700); text-align: right;">Input Value</th>
                            <th style="padding: 10px 15px; font-weight: 600; color: var(--gray-700); text-align: right;">Points</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="border-bottom: 1px solid var(--gray-100); background: #fff5f5;">
                            <td style="padding: 10px 15px; font-weight: 500; color: #c53030;">🔥 Energy</td>
                            <td style="padding: 10px 15px; text-align: right; font-weight: 600; color: var(--gray-800);">${inputs.energy_kj} ${inputs.energy_unit}</td>
                            <td style="padding: 10px 15px; text-align: right; font-weight: 700; color: #c53030;">+${breakdown.energy || 0}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid var(--gray-100); background: #fff5f5;">
                            <td style="padding: 10px 15px; font-weight: 500; color: #c53030;">🧈 Saturated Fat</td>
                            <td style="padding: 10px 15px; text-align: right; font-weight: 600; color: var(--gray-800);">${inputs.sat_fat} g</td>
                            <td style="padding: 10px 15px; text-align: right; font-weight: 700; color: #c53030;">+${breakdown.sat_fat || 0}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid var(--gray-100); background: #fff5f5;">
                            <td style="padding: 10px 15px; font-weight: 500; color: #c53030;">🍞 Sugars</td>
                            <td style="padding: 10px 15px; text-align: right; font-weight: 600; color: var(--gray-800);">${inputs.sugars} g</td>
                            <td style="padding: 10px 15px; text-align: right; font-weight: 700; color: #c53030;">+${breakdown.sugars || 0}</td>
                        </tr>
                        <tr style="border-bottom: 2px solid var(--gray-200); background: #fff5f5;">
                            <td style="padding: 10px 15px; font-weight: 500; color: #c53030;">🧂 Salt</td>
                            <td style="padding: 10px 15px; text-align: right; font-weight: 600; color: var(--gray-800);">${inputs.salt} g</td>
                            <td style="padding: 10px 15px; text-align: right; font-weight: 700; color: #c53030;">+${breakdown.salt || 0}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid var(--gray-100); background: #f0fdf4;">
                            <td style="padding: 10px 15px; font-weight: 500; color: #15803d;">🌾 Dietary Fiber</td>
                            <td style="padding: 10px 15px; text-align: right; font-weight: 600; color: var(--gray-800);">${inputs.fiber} g</td>
                            <td style="padding: 10px 15px; text-align: right; font-weight: 700; color: #15803d;">-${breakdown.fiber || 0}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid var(--gray-100); background: #f0fdf4;">
                            <td style="padding: 10px 15px; font-weight: 500; color: #15803d;">💪 Protein</td>
                            <td style="padding: 10px 15px; text-align: right; font-weight: 600; color: var(--gray-800);">${inputs.protein} g</td>
                            <td style="padding: 10px 15px; text-align: right; font-weight: 700; color: #15803d;">-${breakdown.protein || 0}</td>
                        </tr>
                        <tr style="background: #f0fdf4;">
                            <td style="padding: 10px 15px; font-weight: 500; color: #15803d;">🥦 Fruit, Veg, Nuts</td>
                            <td style="padding: 10px 15px; text-align: right; font-weight: 600; color: var(--gray-800);">${inputs.fruit_veg_percentage}%</td>
                            <td style="padding: 10px 15px; text-align: right; font-weight: 700; color: #15803d;">-${breakdown.fruit_veg || 0}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <div style="margin-top: 8px; font-size: 11px; color: var(--gray-500); font-style: italic;">
                * Note: If Negative Points (A) are 11 or higher, Protein points are only counted if Fruit, Veg & Nuts percentage is high, or if the product is Cheese.
            </div>
        </div>
    `;
    
    content.innerHTML = pointsHtml;
    modal.style.display = 'flex';
}

async function handleCameraCapture() {
    try {
        const imageData = captureFromCamera();
        
        // Show loading
        const loadingOverlay = document.getElementById('loadingOverlay');
        loadingOverlay.style.display = 'flex';
        
        // Send image to server for processing
        const formData = new FormData();
        formData.append('image', dataURLtoBlob(imageData));
        formData.append('type', 'camera');
        
        const response = await fetch('/scan', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showScanResults(result.result);
            updateRecentScans();
            updateStats();
        } else {
            alert('Scan failed: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Camera capture error:', error);
        alert('Camera capture failed: ' + error.message);
    } finally {
        const loadingOverlay = document.getElementById('loadingOverlay');
        loadingOverlay.style.display = 'none';
    }
}

function dataURLtoBlob(dataURL) {
    const arr = dataURL.split(',');
    const mime = arr[0].match(/:(.*?);/)[1];
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while(n--){
        u8arr[n] = bstr.charCodeAt(n);
    }
    return new Blob([u8arr], {type:mime});
}

