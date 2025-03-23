// Initialize global variables
let map;
let vectorLayer;
let popup;
let popupElement;
let popupContent;
let popupCloser;
let chart;
let interconnectionLayer; // New layer for interconnection projects
let interconnectionData; // To store the loaded interconnection data

// ERCOT regions with their approximate coordinates (simplified for visualization)
const ercotRegions = {
    north: {
        name: 'North',
        center: [-97.2, 33.2],
        polygonCoords: [
            [-98.2, 34.0], [-96.5, 34.0], [-96.0, 32.5], [-98.0, 32.2], [-98.2, 34.0]
        ],
        color: 'rgba(0, 128, 255, 0.6)',
        strokeColor: 'rgba(0, 60, 136, 0.8)'
    },
    west: {
        name: 'West',
        center: [-101.5, 32.0],
        polygonCoords: [
            [-103.0, 33.0], [-99.5, 33.0], [-100.0, 30.5], [-103.0, 31.0], [-103.0, 33.0]
        ],
        color: 'rgba(255, 165, 0, 0.6)',
        strokeColor: 'rgba(200, 120, 0, 0.8)'
    },
    south: {
        name: 'South',
        center: [-98.5, 28.5],
        polygonCoords: [
            [-100.0, 30.0], [-97.5, 30.0], [-97.0, 27.0], [-99.5, 27.0], [-100.0, 30.0]
        ],
        color: 'rgba(0, 200, 0, 0.6)',
        strokeColor: 'rgba(0, 120, 0, 0.8)'
    },
    houston: {
        name: 'Houston',
        center: [-95.5, 29.8],
        polygonCoords: [
            [-96.5, 30.5], [-94.5, 30.5], [-94.5, 29.0], [-96.5, 29.0], [-96.5, 30.5]
        ],
        color: 'rgba(255, 0, 0, 0.6)',
        strokeColor: 'rgba(180, 0, 0, 0.8)'
    },
    panhandle: {
        name: 'Panhandle',
        center: [-101.5, 35.5],
        polygonCoords: [
            [-103.0, 36.5], [-100.0, 36.5], [-100.0, 34.5], [-103.0, 34.5], [-103.0, 36.5]
        ],
        color: 'rgba(128, 0, 128, 0.6)',
        strokeColor: 'rgba(80, 0, 80, 0.8)'
    }
};

// Energy type colors for markers
const energyTypeColors = {
    solar: '#FFCC00',
    wind: '#00CCFF',
    gas: '#FF6666',
    battery: '#66CC66',
    other: '#9966CC'
};

// Sample data (will be replaced with actual data loading)
const sampleData = {
    renewableGen: {
        north: { value: 3500, unit: 'MW' },
        west: { value: 8000, unit: 'MW' },
        south: { value: 1200, unit: 'MW' },
        houston: { value: 800, unit: 'MW' },
        panhandle: { value: 4500, unit: 'MW' }
    },
    lmp: {
        north: { value: 35.2, unit: '$/MWh' },
        west: { value: 28.4, unit: '$/MWh' },
        south: { value: 42.7, unit: '$/MWh' },
        houston: { value: 45.1, unit: '$/MWh' },
        panhandle: { value: 25.6, unit: '$/MWh' }
    },
    energyConsumption: {
        north: { value: 15000, unit: 'MWh' },
        west: { value: 8500, unit: 'MWh' },
        south: { value: 12000, unit: 'MWh' },
        houston: { value: 18000, unit: 'MWh' },
        panhandle: { value: 5000, unit: 'MWh' }
    },
    temperature: {
        north: { value: 85, unit: '°F' },
        west: { value: 92, unit: '°F' },
        south: { value: 88, unit: '°F' },
        houston: { value: 90, unit: '°F' },
        panhandle: { value: 78, unit: '°F' }
    }
};

// Initialize the application once DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initMap();
    initPopup();
    setupEventListeners();
    createMapLayers();
    loadInterconnectionData();
    updateUI();
});

// Initialize OpenLayers map
function initMap() {
    map = new ol.Map({
        target: 'map',
        layers: [
            new ol.layer.Tile({
                source: new ol.source.OSM()
            })
        ],
        view: new ol.View({
            center: ol.proj.fromLonLat([-99.5, 31.5]),  // Center of Texas
            zoom: 6
        })
    });
}

// Initialize popup overlay
function initPopup() {
    console.log('Initializing popup overlay');
    
    popupElement = document.getElementById('popup');
    popupContent = document.getElementById('popup-content');
    popupCloser = document.getElementById('popup-closer');
    
    if (!popupElement || !popupContent || !popupCloser) {
        console.error('Popup elements not found in DOM:',
            { popup: !!popupElement, content: !!popupContent, closer: !!popupCloser });
        return;
    }

    // Make sure the popup is initially invisible
    popupElement.style.display = 'block';
    popupElement.style.visibility = 'hidden';
    
    popup = new ol.Overlay({
        element: popupElement,
        positioning: 'bottom-center',
        stopEvent: false,
        offset: [0, -10]
    });
    
    map.addOverlay(popup);
    
    // Store the original setPosition method
    const originalSetPosition = popup.setPosition;
    
    // Override the setPosition method to handle visibility
    popup.setPosition = function(position) {
        originalSetPosition.call(this, position);
        
        if (position === undefined) {
            popupElement.style.visibility = 'hidden';
            console.log('Popup hidden');
        } else {
            popupElement.style.visibility = 'visible';
            console.log('Popup shown at position:', position);
        }
    };
    
    popup.setPosition(undefined); // This will hide the popup
    
    popupCloser.onclick = function() {
        console.log('Popup closed by user');
        popup.setPosition(undefined);
        popupCloser.blur();
        return false;
    };
    
    console.log('Popup initialized');
}

// Set up event listeners
function setupEventListeners() {
    // Map click for showing popup info
    map.on('click', function(evt) {
        const feature = map.forEachFeatureAtPixel(evt.pixel, function(feature) {
            return feature;
        });
        
        if (feature) {
            console.log('Feature clicked:', feature.get('regionKey') || feature.get('projectId'));
            
            if (feature.get('regionKey')) {
                // This is a region feature
                handleRegionClick(feature, evt.coordinate);
            } else if (feature.get('projectId')) {
                // This is an interconnection project feature
                handleProjectClick(feature, evt.coordinate);
            }
        } else {
            popup.setPosition(undefined);
        }
    });
    
    // Add hover functionality for map features
    let lastHoverFeature = null;
    let hoverTimeout = null;
    
    map.on('pointermove', function(evt) {
        if (evt.dragging) {
            return;
        }
        
        const pixel = map.getEventPixel(evt.originalEvent);
        const hit = map.hasFeatureAtPixel(pixel);
        
        map.getTargetElement().style.cursor = hit ? 'pointer' : '';
        
        // Only show hover popup for project features (not regions)
        const feature = map.forEachFeatureAtPixel(pixel, function(feature) {
            return feature;
        });
        
        // Clear popup when moving away from features
        if (!feature) {
            if (lastHoverFeature && lastHoverFeature.get('projectId')) {
                // We only hide the popup after a brief delay
                // to prevent flickering when moving between features
                clearTimeout(hoverTimeout);
                hoverTimeout = setTimeout(() => {
                    // Only hide popup if we're not still on the same feature from the last click
                    const clickedFeatureCoord = popup.getPosition();
                    if (!clickedFeatureCoord) {
                        popup.setPosition(undefined);
                    }
                }, 100);
            }
            lastHoverFeature = null;
            return;
        }
        
        // Clear any pending hide timeout
        clearTimeout(hoverTimeout);
        
        // Handle hover for project features
        if (feature.get('projectId') && feature !== lastHoverFeature) {
            console.log('Hovering over feature:', feature.get('projectId'));
            lastHoverFeature = feature;
            handleProjectHover(feature, evt.coordinate);
        }
    });
    
    // UI controls change events
    document.getElementById('dataType').addEventListener('change', updateUI);
    document.getElementById('region').addEventListener('change', updateUI);
    document.getElementById('date').addEventListener('change', updateUI);
    
    // Interconnection toggle
    document.getElementById('showInterconnection').addEventListener('change', function() {
        toggleInterconnectionLayer(this.checked);
    });
    
    // Energy type filters
    document.querySelectorAll('#solarFilter, #windFilter, #gasFilter, #batteryFilter, #otherFilter')
        .forEach(checkbox => {
            checkbox.addEventListener('change', filterInterconnectionProjects);
        });
    
    // Set initial date to today
    const today = new Date();
    const formattedDate = today.toISOString().split('T')[0];
    document.getElementById('date').value = formattedDate;
}

// Create map layers with ERCOT regions
function createMapLayers() {
    const features = [];
    
    // Create features for each ERCOT region
    for (const [key, region] of Object.entries(ercotRegions)) {
        const polygonCoords = region.polygonCoords.map(coord => ol.proj.fromLonLat(coord));
        
        const feature = new ol.Feature({
            geometry: new ol.geom.Polygon([polygonCoords]),
            name: region.name,
            regionKey: key
        });
        
        features.push(feature);
    }
    
    // Create vector source and layer
    const vectorSource = new ol.source.Vector({
        features: features
    });
    
    vectorLayer = new ol.layer.Vector({
        source: vectorSource,
        style: function(feature) {
            const regionKey = feature.get('regionKey');
            const region = ercotRegions[regionKey];
            
            return new ol.style.Style({
                fill: new ol.style.Fill({
                    color: region.color
                }),
                stroke: new ol.style.Stroke({
                    color: region.strokeColor,
                    width: 2
                }),
                text: new ol.style.Text({
                    text: region.name,
                    font: '14px Calibri,sans-serif',
                    fill: new ol.style.Fill({
                        color: '#000'
                    }),
                    stroke: new ol.style.Stroke({
                        color: '#fff',
                        width: 3
                    })
                })
            });
        }
    });
    
    map.addLayer(vectorLayer);
    
    // Create the interconnection layer (empty for now)
    const interconnectionSource = new ol.source.Vector();
    
    interconnectionLayer = new ol.layer.Vector({
        source: interconnectionSource,
        style: function(feature) {
            // First check if feature should be visible based on filter
            const isVisible = feature.get('_visible');
            
            // If feature is explicitly set to not visible, return null (no style = not rendered)
            if (isVisible === false) {
                return null;
            }
            
            const energyType = feature.get('energyType');
            const capacity = feature.get('capacity');
            
            // Scale marker size based on capacity (between 8 and 18 pixels)
            const size = Math.max(8, Math.min(18, 8 + capacity / 100));
            
            return new ol.style.Style({
                image: new ol.style.Circle({
                    radius: size,
                    fill: new ol.style.Fill({
                        color: energyTypeColors[energyType] || energyTypeColors.other
                    }),
                    stroke: new ol.style.Stroke({
                        color: '#FFFFFF',
                        width: 2
                    })
                })
            });
        },
        visible: false // Initially hidden
    });
    
    map.addLayer(interconnectionLayer);
    
    // Add legend to map
    createLegend();
}

// Create legend for the map
function createLegend() {
    const legendContainer = document.createElement('div');
    legendContainer.className = 'legend';
    legendContainer.innerHTML = '<h4>ERCOT Regions</h4>';
    
    for (const [key, region] of Object.entries(ercotRegions)) {
        const item = document.createElement('div');
        item.className = 'legend-item';
        
        const colorBox = document.createElement('div');
        colorBox.className = 'legend-color';
        colorBox.style.backgroundColor = region.color;
        
        const label = document.createElement('span');
        label.textContent = region.name;
        
        item.appendChild(colorBox);
        item.appendChild(label);
        legendContainer.appendChild(item);
    }
    
    // Add interconnection legend section (hidden initially)
    const interconnectionLegend = document.createElement('div');
    interconnectionLegend.id = 'interconnection-legend';
    interconnectionLegend.style.display = 'none';
    interconnectionLegend.innerHTML = '<h4>Energy Types</h4>';
    
    for (const [type, color] of Object.entries(energyTypeColors)) {
        const item = document.createElement('div');
        item.className = 'legend-item';
        
        const colorBox = document.createElement('div');
        colorBox.className = 'legend-color';
        colorBox.style.backgroundColor = color;
        
        const label = document.createElement('span');
        label.textContent = type.charAt(0).toUpperCase() + type.slice(1);
        
        item.appendChild(colorBox);
        item.appendChild(label);
        interconnectionLegend.appendChild(item);
    }
    
    legendContainer.appendChild(interconnectionLegend);
    document.querySelector('.map').appendChild(legendContainer);
}

// Load interconnection data
function loadInterconnectionData() {
    fetch('data/interconnection_projects.geojson')
        .then(response => response.json())
        .then(data => {
            interconnectionData = data;
            
            // Load summary data for the table
            return fetch('data/interconnection_summary.json');
        })
        .then(response => response.json())
        .then(summary => {
            // Store the summary data
            interconnectionData.summary = summary;
            
            // Now that we have the data, prepare the table
            updateInterconnectionTable(summary.zone_capacity);
        })
        .catch(error => {
            console.error('Error loading interconnection data:', error);
        });
}

// Toggle interconnection layer visibility
function toggleInterconnectionLayer(visible) {
    // Update layer visibility
    interconnectionLayer.setVisible(visible);
    
    // Update legend
    document.getElementById('interconnection-legend').style.display = visible ? 'block' : 'none';
    
    // Update the stats panel
    document.getElementById('statistics').style.display = visible ? 'none' : 'block';
    document.getElementById('interconnection-stats').style.display = visible ? 'block' : 'none';
    
    // If turning on, make sure we have features
    if (visible && interconnectionData && interconnectionLayer.getSource().getFeatures().length === 0) {
        // Add features to the layer
        addInterconnectionFeatures();
    }
    
    // Update the chart if showing interconnection data
    if (visible) {
        updateInterconnectionChart();
    } else {
        // Return to normal data display
        updateUI();
    }
}

// Add interconnection features to the map
function addInterconnectionFeatures() {
    if (!interconnectionData || !interconnectionData.features) return;
    
    const source = interconnectionLayer.getSource();
    source.clear(); // Clear any existing features
    
    // Convert GeoJSON features to OpenLayers features
    interconnectionData.features.forEach(f => {
        const coords = f.geometry.coordinates;
        const properties = f.properties;
        
        const feature = new ol.Feature({
            geometry: new ol.geom.Point(ol.proj.fromLonLat(coords)),
            projectId: properties.id,
            name: properties.name,
            capacity: properties.capacity,
            status: properties.status,
            zone: properties.zone,
            energyType: properties.energy_type
        });
        
        source.addFeature(feature);
    });
    
    // Apply filters
    filterInterconnectionProjects();
}

// Filter interconnection projects based on energy type checkboxes
function filterInterconnectionProjects() {
    if (!interconnectionLayer || !interconnectionLayer.getSource()) return;
    
    const showSolar = document.getElementById('solarFilter').checked;
    const showWind = document.getElementById('windFilter').checked;
    const showGas = document.getElementById('gasFilter').checked;
    const showBattery = document.getElementById('batteryFilter').checked;
    const showOther = document.getElementById('otherFilter').checked;
    
    const features = interconnectionLayer.getSource().getFeatures();
    
    features.forEach(feature => {
        const energyType = feature.get('energyType');
        let visible = false;
        
        switch (energyType) {
            case 'solar':
                visible = showSolar;
                break;
            case 'wind':
                visible = showWind;
                break;
            case 'gas':
                visible = showGas;
                break;
            case 'battery':
                visible = showBattery;
                break;
            case 'other':
                visible = showOther;
                break;
        }
        
        feature.set('_visible', visible);
    });
    
    // Force redraw of the layer with filtered features
    interconnectionLayer.setStyle(interconnectionLayer.getStyle());
    
    // Update the chart with filtered data
    if (interconnectionLayer.getVisible()) {
        updateInterconnectionChart();
    }
}

// Handle region click
function handleRegionClick(feature, coordinate) {
    const regionKey = feature.get('regionKey');
    const region = ercotRegions[regionKey];
    
    // If interconnection layer is visible, show interconnection data
    if (document.getElementById('showInterconnection').checked) {
        // Show interconnection data for this region
        showInterconnectionPopup(regionKey, coordinate);
    } else {
        // Show regular data
        const dataType = document.getElementById('dataType').value;
        const data = sampleData[dataType][regionKey];
        
        popupContent.innerHTML = `
            <h3>${region.name} Region</h3>
            <p><strong>${formatDataTypeLabel(dataType)}:</strong> ${data.value} ${data.unit}</p>
        `;
        
        popup.setPosition(coordinate);
    }
    
    // Update chart with selected region's data
    if (document.getElementById('showInterconnection').checked) {
        updateInterconnectionChart(regionKey);
    } else {
        updateChart(regionKey);
    }
}

// Handle project click
function handleProjectClick(feature, coordinate) {
    console.log('Project clicked:', feature.get('name'), feature.get('projectId'));
    
    const projectId = feature.get('projectId');
    const name = feature.get('name');
    const capacity = feature.get('capacity');
    const status = feature.get('status');
    const zone = feature.get('zone');
    const energyType = feature.get('energyType');
    
    popupContent.innerHTML = `
        <h3>${name}</h3>
        <p><strong>Project ID:</strong> ${projectId}</p>
        <p><strong>Capacity:</strong> ${capacity} MW</p>
        <p><strong>Type:</strong> ${energyType.charAt(0).toUpperCase() + energyType.slice(1)}</p>
        <p><strong>Status:</strong> ${status}</p>
        <p><strong>Zone:</strong> ${zone.charAt(0).toUpperCase() + zone.slice(1)}</p>
    `;
    
    popup.setPosition(coordinate);
}

// Show interconnection popup for a region
function showInterconnectionPopup(regionKey, coordinate) {
    if (!interconnectionData || !interconnectionData.summary) return;
    
    const region = ercotRegions[regionKey];
    const zoneData = interconnectionData.summary.zone_capacity[regionKey];
    
    if (!zoneData) return;
    
    // Calculate total capacity
    let totalCapacity = 0;
    Object.values(zoneData).forEach(cap => totalCapacity += cap);
    
    // Create popup content
    let popupHtml = `
        <h3>${region.name} Region Interconnection Queue</h3>
        <p><strong>Total Capacity:</strong> ${Math.round(totalCapacity).toLocaleString()} MW</p>
        <table style="width:100%; border-collapse: collapse; margin-top: 10px;">
            <tr>
                <th style="text-align:left; padding: 4px;">Energy Type</th>
                <th style="text-align:right; padding: 4px;">Capacity (MW)</th>
                <th style="text-align:right; padding: 4px;">% of Total</th>
            </tr>
    `;
    
    // Add a row for each energy type
    for (const [type, capacity] of Object.entries(zoneData)) {
        if (capacity > 0) {
            const percent = Math.round((capacity / totalCapacity) * 100);
            const bgColor = type === 'total' ? '#f8f9fa' : 'transparent';
            const fontWeight = type === 'total' ? 'bold' : 'normal';
            
            popupHtml += `
                <tr style="background-color: ${bgColor}; font-weight: ${fontWeight};">
                    <td style="text-align:left; padding: 4px;">${type.charAt(0).toUpperCase() + type.slice(1)}</td>
                    <td style="text-align:right; padding: 4px;">${Math.round(capacity).toLocaleString()}</td>
                    <td style="text-align:right; padding: 4px;">${percent}%</td>
                </tr>
            `;
        }
    }
    
    popupHtml += `</table>`;
    
    popupContent.innerHTML = popupHtml;
    popup.setPosition(coordinate);
}

// Update UI based on selected options
function updateUI() {
    const dataType = document.getElementById('dataType').value;
    const selectedRegion = document.getElementById('region').value;
    const date = document.getElementById('date').value;
    
    updateDataDisplay(dataType, selectedRegion, date);
    updateStatistics(dataType, selectedRegion);
    
    if (selectedRegion === 'all') {
        // Show all regions
        updateChart('all');
    } else {
        // Show specific region
        updateChart(selectedRegion);
    }
}

// Update the data display (highlight selected regions, etc.)
function updateDataDisplay(dataType, selectedRegion, date) {
    // Update map styles based on selected region
    vectorLayer.getSource().getFeatures().forEach(feature => {
        const regionKey = feature.get('regionKey');
        const region = ercotRegions[regionKey];
        
        let fillColor = region.color;
        let strokeWidth = 2;
        
        // Highlight selected region or show all if "all" is selected
        if (selectedRegion !== 'all' && regionKey !== selectedRegion) {
            fillColor = 'rgba(200, 200, 200, 0.4)'; // Dim non-selected regions
        } else if (selectedRegion === regionKey) {
            strokeWidth = 4; // Thicker border for selected region
        }
        
        feature.setStyle(new ol.style.Style({
            fill: new ol.style.Fill({
                color: fillColor
            }),
            stroke: new ol.style.Stroke({
                color: region.strokeColor,
                width: strokeWidth
            }),
            text: new ol.style.Text({
                text: region.name,
                font: '14px Calibri,sans-serif',
                fill: new ol.style.Fill({
                    color: '#000'
                }),
                stroke: new ol.style.Stroke({
                    color: '#fff',
                    width: 3
                })
            })
        }));
    });
}

// Update statistics display
function updateStatistics(dataType, selectedRegion) {
    let avgConsumption = 0;
    let peakGeneration = 0;
    let avgLmp = 0;
    
    if (selectedRegion === 'all') {
        // Calculate averages across all regions
        Object.values(sampleData.energyConsumption).forEach(data => {
            avgConsumption += data.value;
        });
        avgConsumption /= Object.keys(ercotRegions).length;
        
        // Find peak generation across all regions
        Object.values(sampleData.renewableGen).forEach(data => {
            peakGeneration = Math.max(peakGeneration, data.value);
        });
        
        // Calculate average LMP across all regions
        Object.values(sampleData.lmp).forEach(data => {
            avgLmp += data.value;
        });
        avgLmp /= Object.keys(ercotRegions).length;
    } else {
        // Use values for the selected region
        avgConsumption = sampleData.energyConsumption[selectedRegion].value;
        peakGeneration = sampleData.renewableGen[selectedRegion].value;
        avgLmp = sampleData.lmp[selectedRegion].value;
    }
    
    // Update the statistics display
    document.getElementById('avg-consumption').textContent = 
        `${avgConsumption.toLocaleString()} MWh`;
    document.getElementById('peak-generation').textContent = 
        `${peakGeneration.toLocaleString()} MW`;
    document.getElementById('avg-lmp').textContent = 
        `$${avgLmp.toFixed(2)}/MWh`;
}

// Update chart with selected data
function updateChart(selectedRegion) {
    const dataType = document.getElementById('dataType').value;
    const chartData = {
        labels: [],
        datasets: [{
            label: formatDataTypeLabel(dataType),
            data: [],
            backgroundColor: [],
            borderColor: [],
            borderWidth: 1
        }]
    };
    
    if (selectedRegion === 'all') {
        // Show data for all regions
        for (const [key, region] of Object.entries(ercotRegions)) {
            chartData.labels.push(region.name);
            chartData.datasets[0].data.push(sampleData[dataType][key].value);
            chartData.datasets[0].backgroundColor.push(region.color);
            chartData.datasets[0].borderColor.push(region.strokeColor);
        }
    } else {
        // Show hourly data for selected region (simulated)
        const hoursInDay = 24;
        for (let i = 0; i < hoursInDay; i++) {
            chartData.labels.push(`${i}:00`);
            
            // Generate some variation based on the actual value
            const baseValue = sampleData[dataType][selectedRegion].value;
            const hourlyValue = baseValue * (0.7 + 0.6 * Math.sin(i * Math.PI / 12));
            
            chartData.datasets[0].data.push(hourlyValue);
            chartData.datasets[0].backgroundColor.push(ercotRegions[selectedRegion].color);
            chartData.datasets[0].borderColor.push(ercotRegions[selectedRegion].strokeColor);
        }
    }
    
    // Update or create chart
    updateChartElement(chartData, selectedRegion === 'all' ? 'bar' : 'line');
}

// Update interconnection chart with filtered data
function updateInterconnectionChart(selectedRegion = null) {
    if (!interconnectionData || !interconnectionData.summary) return;
    
    const zoneCapacity = interconnectionData.summary.zone_capacity;
    
    // Create chart data
    let chartData;
    let chartType;
    
    if (selectedRegion === null || selectedRegion === 'all') {
        // Show capacity by region and energy type
        chartData = createRegionCapacityChartData(zoneCapacity);
        chartType = 'bar';
    } else {
        // Show breakdown for the selected region
        chartData = createEnergyTypeChartData(zoneCapacity[selectedRegion]);
        chartType = 'pie';
    }
    
    // Update the chart
    updateChartElement(chartData, chartType);
}

// Create chart data for region capacity
function createRegionCapacityChartData(zoneCapacity) {
    const energyTypes = ['solar', 'wind', 'gas', 'battery', 'other'];
    const datasets = [];
    const labels = Object.keys(zoneCapacity).map(zone => 
        zone.charAt(0).toUpperCase() + zone.slice(1));
    
    // Create a dataset for each energy type
    energyTypes.forEach((type, index) => {
        // Check if the type is filtered out
        const isVisible = document.getElementById(`${type}Filter`).checked;
        if (!isVisible) return;
        
        const data = Object.values(zoneCapacity).map(zone => zone[type]);
        
        datasets.push({
            label: type.charAt(0).toUpperCase() + type.slice(1),
            data: data,
            backgroundColor: energyTypeColors[type],
            borderColor: 'rgba(255, 255, 255, 0.8)',
            borderWidth: 1
        });
    });
    
    return {
        labels: labels,
        datasets: datasets
    };
}

// Create chart data for energy type breakdown
function createEnergyTypeChartData(regionData) {
    const labels = [];
    const data = [];
    const backgroundColor = [];
    const borderColor = [];
    
    // Add each energy type that is visible
    for (const [type, capacity] of Object.entries(regionData)) {
        // Skip if type is filtered out
        if (!document.getElementById(`${type}Filter`).checked) continue;
        
        // Skip if no capacity
        if (capacity <= 0) continue;
        
        labels.push(type.charAt(0).toUpperCase() + type.slice(1));
        data.push(capacity);
        backgroundColor.push(energyTypeColors[type]);
        borderColor.push('white');
    }
    
    return {
        labels: labels,
        datasets: [{
            data: data,
            backgroundColor: backgroundColor,
            borderColor: borderColor,
            borderWidth: 1
        }]
    };
}

// Update chart element
function updateChartElement(chartData, chartType) {
    const ctx = document.getElementById('chart').getContext('2d');
    
    if (chart) {
        chart.destroy();
    }
    
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {}
    };
    
    // Configure scales based on chart type
    if (chartType === 'bar') {
        chartOptions.scales.y = {
            beginAtZero: true,
            stacked: true,
            title: {
                display: true,
                text: 'Capacity (MW)'
            }
        };
        chartOptions.scales.x = {
            stacked: true
        };
    }
    
    // For pie charts, add some additional options
    if (chartType === 'pie') {
        chartOptions.plugins = {
            legend: {
                position: 'right'
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const value = context.raw;
                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                        const percentage = Math.round((value / total) * 100);
                        return `${context.label}: ${Math.round(value).toLocaleString()} MW (${percentage}%)`;
                    }
                }
            }
        };
    }
    
    chart = new Chart(ctx, {
        type: chartType,
        data: chartData,
        options: chartOptions
    });
}

// Update interconnection capacity table
function updateInterconnectionTable(zoneCapacity) {
    const tableBody = document.querySelector('#interconnection-table tbody');
    tableBody.innerHTML = '';
    
    // Calculate column totals
    const columnTotals = {
        solar: 0,
        wind: 0,
        gas: 0,
        battery: 0,
        other: 0,
        total: 0
    };
    
    // Add rows for each zone
    for (const [zone, capacities] of Object.entries(zoneCapacity)) {
        // Calculate row total
        let rowTotal = 0;
        for (const [type, capacity] of Object.entries(capacities)) {
            rowTotal += capacity;
            columnTotals[type] += capacity;
        }
        columnTotals.total += rowTotal;
        
        // Create row
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${zone.charAt(0).toUpperCase() + zone.slice(1)}</td>
            <td>${Math.round(capacities.solar).toLocaleString()}</td>
            <td>${Math.round(capacities.wind).toLocaleString()}</td>
            <td>${Math.round(capacities.gas).toLocaleString()}</td>
            <td>${Math.round(capacities.battery).toLocaleString()}</td>
            <td>${Math.round(capacities.other).toLocaleString()}</td>
            <td>${Math.round(rowTotal).toLocaleString()}</td>
        `;
        
        tableBody.appendChild(row);
    }
    
    // Add totals row
    const totalsRow = document.createElement('tr');
    totalsRow.className = 'highlight';
    totalsRow.innerHTML = `
        <td>Total</td>
        <td>${Math.round(columnTotals.solar).toLocaleString()}</td>
        <td>${Math.round(columnTotals.wind).toLocaleString()}</td>
        <td>${Math.round(columnTotals.gas).toLocaleString()}</td>
        <td>${Math.round(columnTotals.battery).toLocaleString()}</td>
        <td>${Math.round(columnTotals.other).toLocaleString()}</td>
        <td>${Math.round(columnTotals.total).toLocaleString()}</td>
    `;
    
    tableBody.appendChild(totalsRow);
}

// Helper function to format data type labels
function formatDataTypeLabel(dataType) {
    switch(dataType) {
        case 'renewableGen':
            return 'Renewable Generation';
        case 'lmp':
            return 'Locational Marginal Price';
        case 'energyConsumption':
            return 'Energy Consumption';
        case 'temperature':
            return 'Temperature';
        default:
            return dataType;
    }
}

// Function to load actual data (to be implemented)
function loadActualData() {
    // This would be replaced with actual data loading from ERCOT CSV files
    // For now we just use the sample data
    return sampleData;
}

// To be implemented: Function to create a data processing script
function createDataProcessor() {
    // This would create a Python script to process ERCOT data
    console.log('Data processor would be created here');
    
    // Example of data that would be processed:
    // - Load generation data from ercot_gen_sun-wnd_5min_2025Q1.csv
    // - Load LMP data from ercot_lmp_rt_15min_hubs_2025Q1.csv
    // - Process and aggregate data by region
    // - Output JSON files for the web visualization
}

// Handle project hover
function handleProjectHover(feature, coordinate) {
    console.log('Project hover:', feature.get('name'), feature.get('projectId'));
    
    if (!interconnectionLayer.getVisible()) return;
    
    const projectId = feature.get('projectId');
    const name = feature.get('name');
    const capacity = feature.get('capacity');
    const status = feature.get('status');
    const zone = feature.get('zone');
    const energyType = feature.get('energyType');
    
    popupContent.innerHTML = `
        <h3>${name}</h3>
        <p><strong>Project ID:</strong> ${projectId}</p>
        <p><strong>Capacity:</strong> ${capacity} MW</p>
        <p><strong>Type:</strong> ${energyType.charAt(0).toUpperCase() + energyType.slice(1)}</p>
        <p><strong>Status:</strong> ${status}</p>
        <p><strong>Zone:</strong> ${zone.charAt(0).toUpperCase() + zone.slice(1)}</p>
    `;
    
    popup.setPosition(coordinate);
} 