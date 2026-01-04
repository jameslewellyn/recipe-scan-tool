        // Tab switching functionality
        const tabs = document.querySelectorAll('.tab');
        const tabContents = document.querySelectorAll('.tab-content');

        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const targetTab = this.getAttribute('data-tab');
                
                // Remove active class from all tabs and contents
                tabs.forEach(t => t.classList.remove('active'));
                tabContents.forEach(tc => tc.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding content
                this.classList.add('active');
                document.getElementById(`${targetTab}-tab`).classList.add('active');
                
                // Load recipes when View tab is clicked
                if (targetTab === 'view') {
                    loadRecipes();
                }
            });
        });

        // Upload tab functionality
        const pdfInput = document.getElementById('pdfInput');
        const selectedFiles = document.getElementById('selectedFiles');
        const fileCountText = document.getElementById('fileCountText');
        const uploadButton = document.getElementById('uploadButton');
        const filesList = document.getElementById('filesList');
        const fileCount = document.getElementById('fileCount');
        const loading = document.getElementById('loading');
        const emptyState = document.getElementById('emptyState');
        const errorMessage = document.getElementById('errorMessage');
        const uploadResults = document.getElementById('uploadResults');
        const progressContainer = document.getElementById('progressContainer');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');

        let selectedFilesList = [];

        pdfInput.addEventListener('change', function(e) {
            const files = Array.from(e.target.files).filter(f => f.name.toLowerCase().endsWith('.pdf'));
            
            if (files.length === 0) {
                selectedFiles.style.display = 'none';
                uploadButton.style.display = 'none';
                filesList.style.display = 'none';
                emptyState.style.display = 'block';
                return;
            }

            selectedFilesList = files;
            
            // Display selected files count
            fileCountText.textContent = `${files.length} PDF file${files.length !== 1 ? 's' : ''} selected`;
            selectedFiles.style.display = 'block';
            uploadButton.style.display = 'block';

            // Hide error message
            errorMessage.style.display = 'none';

            // Display files
            displayFiles(files);
        });

        uploadButton.addEventListener('click', async function() {
            if (selectedFilesList.length === 0) return;

            // Hide previous results
            uploadResults.style.display = 'none';
            uploadResults.innerHTML = '<h3 style="padding: 15px 20px; background: #f0f0f0; margin: 0;">Upload Results</h3>';

            // Show progress bar
            progressContainer.classList.add('active');
            loading.style.display = 'none';
            uploadButton.disabled = true;
            uploadButton.textContent = 'Processing...';

            // Initialize progress
            progressBar.style.width = '0%';
            progressBar.textContent = '0%';
            progressText.textContent = 'Starting upload...';

            const totalFiles = selectedFilesList.length;
            const allResults = [];

            // Process files one at a time to show progress
            for (let i = 0; i < totalFiles; i++) {
                const file = selectedFilesList[i];
                const fileNum = i + 1;
                
                // Update progress before processing
                const progressBefore = Math.round((i / totalFiles) * 100);
                progressBar.style.width = progressBefore + '%';
                progressBar.textContent = progressBefore + '%';
                progressText.textContent = `Processing file ${fileNum} of ${totalFiles}: ${file.name}`;

                try {
                    const formData = new FormData();
                    formData.append('files', file);

                    const response = await fetch('/api/upload-pdfs', {
                        method: 'POST',
                        body: formData
                    });

                    const data = await response.json();

                    if (!response.ok) {
                        throw new Error(data.error || 'Upload failed');
                    }

                    // Add results
                    if (data.results && data.results.length > 0) {
                        allResults.push(...data.results);
                    }

                    // Update progress after file completes
                    const progressAfter = Math.round((fileNum / totalFiles) * 100);
                    progressBar.style.width = progressAfter + '%';
                    progressBar.textContent = progressAfter + '%';
                    progressText.textContent = `Completed file ${fileNum} of ${totalFiles}: ${file.name}`;

                } catch (error) {
                    allResults.push({
                        filename: file.name,
                        status: 'error',
                        error: error.message
                    });
                    
                    // Update progress even on error
                    const progressAfter = Math.round((fileNum / totalFiles) * 100);
                    progressBar.style.width = progressAfter + '%';
                    progressBar.textContent = progressAfter + '%';
                    progressText.textContent = `Error processing file ${fileNum} of ${totalFiles}: ${file.name}`;
                }
            }

            // Final progress update
            progressBar.style.width = '100%';
            progressBar.textContent = '100%';
            progressText.textContent = 'Processing complete!';

            // Display results
            displayUploadResults(allResults);

            // Hide progress after a short delay
            setTimeout(() => {
                progressContainer.classList.remove('active');
                uploadButton.disabled = false;
                uploadButton.textContent = 'Upload to Database';
            }, 1000);
        });

        function displayFiles(files) {
            if (files.length === 0) {
                emptyState.style.display = 'block';
                filesList.style.display = 'none';
                fileCount.style.display = 'none';
                return;
            }

            // Sort files by name
            files.sort((a, b) => a.name.localeCompare(b.name));

            // Display file count
            fileCount.textContent = `${files.length} file${files.length !== 1 ? 's' : ''}`;
            fileCount.style.display = 'block';

            // Clear and populate file list
            filesList.innerHTML = '';
            files.forEach(file => {
                const fileItem = createFileItem(file);
                filesList.appendChild(fileItem);
            });

            filesList.style.display = 'block';
            emptyState.style.display = 'none';
        }

        function displayUploadResults(results) {
            uploadResults.style.display = 'block';
            
            results.forEach(result => {
                const item = document.createElement('div');
                item.className = 'file-item';
                
                let statusClass = '';
                let statusIcon = '';
                if (result.status === 'success') {
                    statusClass = 'success';
                    statusIcon = '✅';
                } else if (result.status === 'duplicate') {
                    statusClass = 'warning';
                    statusIcon = '⚠️';
                } else {
                    statusClass = 'error';
                    statusIcon = '❌';
                }
                
                item.innerHTML = `
                    <div class="file-info">
                        <div class="file-name">${statusIcon} ${result.filename}</div>
                        <div class="file-details">
                            ${result.message || result.error || ''}
                            ${result.recipe_id ? ` (Recipe ID: ${result.recipe_id})` : ''}
                        </div>
                    </div>
                    <span class="file-extension" style="background: ${result.status === 'success' ? '#4caf50' : result.status === 'duplicate' ? '#ff9800' : '#f44336'}">
                        ${result.status.toUpperCase()}
                    </span>
                `;
                
                uploadResults.appendChild(item);
            });
        }

        function createFileItem(file) {
            const item = document.createElement('div');
            item.className = 'file-item';

            const fileInfo = document.createElement('div');
            fileInfo.className = 'file-info';

            const fileName = document.createElement('div');
            fileName.className = 'file-name';
            fileName.textContent = file.name;

            const fileDetails = document.createElement('div');
            fileDetails.className = 'file-details';
            fileDetails.innerHTML = `
                <span class="format-size">${formatFileSize(file.size)}</span>
            `;

            fileInfo.appendChild(fileName);
            fileInfo.appendChild(fileDetails);

            const extension = document.createElement('span');
            extension.className = 'file-extension';
            const ext = getFileExtension(file.name);
            extension.textContent = ext || 'FILE';

            item.appendChild(fileInfo);
            item.appendChild(extension);

            return item;
        }

        function getFileExtension(filename) {
            const parts = filename.split('.');
            return parts.length > 1 ? parts[parts.length - 1].toUpperCase() : '';
        }

        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
        }

        function showError(message) {
            errorMessage.textContent = message;
            errorMessage.style.display = 'block';
            loading.style.display = 'none';
        }

        // View tab functionality
        const viewLoading = document.getElementById('viewLoading');
        const viewError = document.getElementById('viewError');
        const recipesTableContainer = document.getElementById('recipesTableContainer');
        const recipesTableBody = document.getElementById('recipesTableBody');
        const recipeCount = document.getElementById('recipeCount');
        const viewEmptyState = document.getElementById('viewEmptyState');
        const recipeFilter = document.getElementById('recipeFilter');
        
        // Store all recipes for filtering
        let allRecipes = [];
        
        // Pagination state
        let currentPage = 1;
        let pageSize = 10;
        let filteredRecipes = [];
        
        // Tag filtering state
        let allTags = [];
        let selectedTagIds = new Set(); // All tags selected by default
        let includeUntagged = true; // Include untagged recipes by default
        
        // State filtering state
        const allStates = [
            { value: 'not_started', label: 'Not Started', emoji: '⏳' },
            { value: 'partially_complete', label: 'In Progress', emoji: '🔄' },
            { value: 'complete', label: 'Complete', emoji: '✅' },
            { value: 'broken', label: 'Broken', emoji: '❌' },
            { value: 'duplicate', label: 'Duplicate', emoji: '📋' }
        ];
        let selectedStates = new Set(allStates.map(s => s.value)); // All states selected by default

        // State persistence functions
        function saveViewState() {
            try {
                const state = {
                    currentPage: currentPage,
                    pageSize: pageSize,
                    filterText: recipeFilter ? recipeFilter.value : '',
                    selectedTagIds: Array.from(selectedTagIds),
                    includeUntagged: includeUntagged,
                    selectedStates: Array.from(selectedStates)
                };
                localStorage.setItem('recipeViewState', JSON.stringify(state));
            } catch (error) {
                console.error('Error saving view state:', error);
            }
        }

        function loadViewState() {
            try {
                const saved = localStorage.getItem('recipeViewState');
                if (saved) {
                    const state = JSON.parse(saved);
                    if (state.currentPage) currentPage = state.currentPage;
                    if (state.pageSize) {
                        pageSize = state.pageSize;
                        const pageSizeSelect = document.getElementById('pageSizeSelect');
                        if (pageSizeSelect) {
                            pageSizeSelect.value = pageSize;
                        }
                    }
                    if (state.filterText !== undefined && recipeFilter) {
                        recipeFilter.value = state.filterText;
                    }
                    if (state.selectedTagIds && allTags.length > 0) {
                        // Only restore tag IDs that still exist
                        const validTagIds = allTags.map(tag => tag.id);
                        selectedTagIds = new Set(state.selectedTagIds.filter(id => validTagIds.includes(id)));
                    }
                    if (typeof state.includeUntagged === 'boolean') {
                        includeUntagged = state.includeUntagged;
                    }
                    if (state.selectedStates) {
                        // Only restore states that are valid
                        const validStates = allStates.map(s => s.value);
                        selectedStates = new Set(state.selectedStates.filter(s => validStates.includes(s)));
                    }
                    return true;
                }
            } catch (error) {
                console.error('Error loading view state:', error);
            }
            return false;
        }

        // Fuzzy match function - checks if search string appears in order in the target string
        function fuzzyMatch(search, target) {
            if (!search || search.trim() === '') return true;
            if (!target) return false;
            
            const searchLower = search.toLowerCase().trim();
            const targetLower = target.toLowerCase();
            
            // Simple substring match
            if (targetLower.includes(searchLower)) return true;
            
            // Fuzzy match: check if all characters in search appear in order in target
            let searchIndex = 0;
            for (let i = 0; i < targetLower.length && searchIndex < searchLower.length; i++) {
                if (targetLower[i] === searchLower[searchIndex]) {
                    searchIndex++;
                }
            }
            return searchIndex === searchLower.length;
        }

        function filterRecipes(recipes, filterText, selectedTagIdsSet, includeUntaggedFlag = true, selectedStatesSet = null) {
            let filtered = recipes;
            
            // Filter by title
            if (filterText && filterText.trim() !== '') {
                filtered = filtered.filter(recipe => {
                    const title = recipe.title || recipe.pdf_filename || '';
                    return fuzzyMatch(filterText, title);
                });
            }
            
            // Filter by tags
            // If tags are selected, show recipes that have at least one of the selected tags
            // Also include untagged recipes if includeUntaggedFlag is true
            if (selectedTagIdsSet && selectedTagIdsSet.size > 0) {
                filtered = filtered.filter(recipe => {
                    const hasTags = recipe.tags && recipe.tags.length > 0;
                    if (!hasTags) {
                        return includeUntaggedFlag; // Show untagged recipes if includeUntaggedFlag is true
                    }
                    // Check if recipe has any of the selected tags
                    return recipe.tags.some(tag => selectedTagIdsSet.has(tag.id));
                });
            } else if (selectedTagIdsSet && selectedTagIdsSet.size === 0) {
                // No tags selected - only show untagged recipes if includeUntaggedFlag is true
                filtered = filtered.filter(recipe => {
                    const hasTags = recipe.tags && recipe.tags.length > 0;
                    return !hasTags && includeUntaggedFlag;
                });
            }
            // If selectedTagIdsSet is null/undefined, show all recipes (no tag filtering)
            
            // Filter by state
            if (selectedStatesSet && selectedStatesSet.size > 0) {
                filtered = filtered.filter(recipe => {
                    const recipeState = recipe.state || 'not_started';
                    return selectedStatesSet.has(recipeState);
                });
            } else if (selectedStatesSet && selectedStatesSet.size === 0) {
                // If no states are selected, show no recipes
                filtered = [];
            }
            // If selectedStatesSet is null/undefined, show all recipes (no state filtering)
            
            return filtered;
        }

        async function loadRecipes() {
            viewLoading.style.display = 'block';
            viewError.style.display = 'none';
            recipesTableContainer.style.display = 'none';
            viewEmptyState.style.display = 'none';

            try {
                // Load recipes and tags in parallel
                const [recipesResponse, tagsResponse] = await Promise.all([
                    fetch('/api/recipes'),
                    fetch('/api/tags')
                ]);

                const recipesData = await recipesResponse.json();
                const tagsData = await tagsResponse.json();

                if (!recipesResponse.ok) {
                    throw new Error(recipesData.error || 'Failed to load recipes');
                }

                // Store all recipes (tags are already included from the API)
                allRecipes = recipesData.recipes;
                
                // Load and display tags
                if (tagsData.tags) {
                    allTags = tagsData.tags;
                    // Select all tags by default, and include untagged
                    selectedTagIds = new Set(allTags.map(tag => tag.id));
                    includeUntagged = true;
                }
                
                // Initialize state filter (all states selected by default)
                selectedStates = new Set(allStates.map(s => s.value));
                
                // Load persisted state (overrides defaults if available)
                const hasPersistedState = loadViewState();
                
                // Render filters after loading state
                renderTagFilter();
                renderStateFilter();
                
                // Apply current filter if any
                const filterText = recipeFilter ? recipeFilter.value : '';
                filteredRecipes = filterRecipes(allRecipes, filterText, selectedTagIds, includeUntagged, selectedStates);
                // Preserve current page instead of resetting (or use persisted page)
                const totalPages = Math.max(1, Math.ceil(filteredRecipes.length / pageSize));
                if (currentPage > totalPages) {
                    currentPage = totalPages;
                }
                
                displayRecipes(filteredRecipes);
                // Only save state if we didn't just load it (to avoid overwriting with defaults)
                if (!hasPersistedState) {
                    saveViewState();
                }
            } catch (error) {
                viewError.textContent = 'Error loading recipes: ' + error.message;
                viewError.style.display = 'block';
            } finally {
                viewLoading.style.display = 'none';
            }
        }
        
        // Add filter event listener
        if (recipeFilter) {
            recipeFilter.addEventListener('input', function() {
                const filterText = this.value;
                const savedPage = currentPage;
                filteredRecipes = filterRecipes(allRecipes, filterText, selectedTagIds, includeUntagged, selectedStates);
                // Preserve page if possible, otherwise reset to 1
                const totalPages = Math.max(1, Math.ceil(filteredRecipes.length / pageSize));
                if (savedPage <= totalPages) {
                    currentPage = savedPage;
                } else {
                    currentPage = 1;
                }
                displayRecipes(filteredRecipes);
                saveViewState();
            });
        }

        // Tag filter functions
        function renderTagFilter() {
            const dropdown = document.getElementById('tagFilterDropdown');
            if (!dropdown) return;
            
            // Count untagged recipes
            const untaggedCount = allRecipes.filter(recipe => !recipe.tags || recipe.tags.length === 0).length;
            
            let html = '';
            
            // Add "Untagged" option first (special styling)
            html += `
                <div class="tag-filter-item tag-filter-item-untagged">
                    <input type="checkbox" class="tag-filter-checkbox" id="tag-untagged" value="untagged" ${includeUntagged ? 'checked' : ''}>
                    <label class="tag-filter-label" for="tag-untagged">
                        <span class="tag-filter-untagged-text">🏷️ <strong>Untagged</strong></span>
                        <span class="tag-filter-count">${untaggedCount}</span>
                    </label>
                </div>
            `;
            
            // Add regular tags
            if (allTags.length > 0) {
                html += allTags.map(tag => `
                    <div class="tag-filter-item">
                        <input type="checkbox" class="tag-filter-checkbox" id="tag-${tag.id}" value="${tag.id}" ${selectedTagIds.has(tag.id) ? 'checked' : ''}>
                        <label class="tag-filter-label" for="tag-${tag.id}">
                            <span>${escapeHtml(tag.tag_name)}</span>
                            <span class="tag-filter-count">${tag.recipe_count}</span>
                        </label>
                    </div>
                `).join('');
            } else {
                html += '<div style="padding: 8px; color: #999; text-align: center;">No tags available</div>';
            }
            
            dropdown.innerHTML = html;
            
            // Add event listeners to checkboxes
            dropdown.querySelectorAll('.tag-filter-checkbox').forEach(checkbox => {
                checkbox.addEventListener('change', function() {
                    if (this.value === 'untagged') {
                        includeUntagged = this.checked;
                    } else {
                        const tagId = parseInt(this.value, 10);
                        if (this.checked) {
                            selectedTagIds.add(tagId);
                        } else {
                            selectedTagIds.delete(tagId);
                        }
                    }
                    applyTagFilter();
                });
            });
            
            updateTagFilterToggleText();
        }

        function updateTagFilterToggleText() {
            const toggle = document.getElementById('tagFilterToggle');
            if (!toggle) return;
            
            const totalOptions = allTags.length + 1; // tags + untagged
            const selectedCount = selectedTagIds.size + (includeUntagged ? 1 : 0);
            
            if (selectedCount === 0) {
                toggle.textContent = 'No options selected';
            } else if (selectedCount === totalOptions) {
                toggle.textContent = 'All selected';
            } else {
                toggle.textContent = `${selectedCount} option${selectedCount !== 1 ? 's' : ''} selected`;
            }
        }

        function applyTagFilter() {
            const filterText = recipeFilter ? recipeFilter.value : '';
            const savedPage = currentPage;
            filteredRecipes = filterRecipes(allRecipes, filterText, selectedTagIds, includeUntagged, selectedStates);
            // Preserve page if possible, otherwise reset to 1
            const totalPages = Math.max(1, Math.ceil(filteredRecipes.length / pageSize));
            if (savedPage <= totalPages) {
                currentPage = savedPage;
            } else {
                currentPage = 1;
            }
            displayRecipes(filteredRecipes);
            updateTagFilterToggleText();
            saveViewState();
        }

        // State filter functions
        function renderStateFilter() {
            const dropdown = document.getElementById('stateFilterDropdown');
            if (!dropdown) return;
            
            // Count recipes for each state
            const stateCounts = {};
            allRecipes.forEach(recipe => {
                const state = recipe.state || 'not_started';
                stateCounts[state] = (stateCounts[state] || 0) + 1;
            });
            
            dropdown.innerHTML = allStates.map(state => {
                const count = stateCounts[state.value] || 0;
                return `
                    <div class="tag-filter-item">
                        <input type="checkbox" class="tag-filter-checkbox" id="state-${state.value}" value="${state.value}" ${selectedStates.has(state.value) ? 'checked' : ''}>
                        <label class="tag-filter-label" for="state-${state.value}">
                            <span>${state.emoji} ${state.label}</span>
                            <span class="tag-filter-count">${count}</span>
                        </label>
                    </div>
                `;
            }).join('');
            
            // Add event listeners to checkboxes
            dropdown.querySelectorAll('.tag-filter-checkbox').forEach(checkbox => {
                checkbox.addEventListener('change', function() {
                    const stateValue = this.value;
                    if (this.checked) {
                        selectedStates.add(stateValue);
                    } else {
                        selectedStates.delete(stateValue);
                    }
                    applyStateFilter();
                });
            });
            
            updateStateFilterToggleText();
        }

        function updateStateFilterToggleText() {
            const toggle = document.getElementById('stateFilterToggle');
            if (!toggle) return;
            
            if (selectedStates.size === 0) {
                toggle.textContent = 'No states selected';
            } else if (selectedStates.size === allStates.length) {
                toggle.textContent = 'All states selected';
            } else {
                toggle.textContent = `${selectedStates.size} state${selectedStates.size !== 1 ? 's' : ''} selected`;
            }
        }

        function applyStateFilter() {
            const filterText = recipeFilter ? recipeFilter.value : '';
            const savedPage = currentPage;
            filteredRecipes = filterRecipes(allRecipes, filterText, selectedTagIds, includeUntagged, selectedStates);
            // Preserve page if possible, otherwise reset to 1
            const totalPages = Math.max(1, Math.ceil(filteredRecipes.length / pageSize));
            if (savedPage <= totalPages) {
                currentPage = savedPage;
            } else {
                currentPage = 1;
            }
            displayRecipes(filteredRecipes);
            updateStateFilterToggleText();
            saveViewState();
        }

        // Tag filter UI event handlers
        const tagFilterToggle = document.getElementById('tagFilterToggle');
        const tagFilterDropdown = document.getElementById('tagFilterDropdown');
        const selectAllTagsBtn = document.getElementById('selectAllTagsBtn');
        const deselectAllTagsBtn = document.getElementById('deselectAllTagsBtn');

        if (tagFilterToggle && tagFilterDropdown) {
            tagFilterToggle.addEventListener('click', function() {
                const isActive = tagFilterDropdown.classList.contains('active');
                if (isActive) {
                    tagFilterDropdown.classList.remove('active');
                    tagFilterToggle.classList.remove('active');
                } else {
                    tagFilterDropdown.classList.add('active');
                    tagFilterToggle.classList.add('active');
                }
            });
        }

        if (selectAllTagsBtn) {
            selectAllTagsBtn.addEventListener('click', function() {
                selectedTagIds = new Set(allTags.map(tag => tag.id));
                includeUntagged = true;
                renderTagFilter();
                applyTagFilter();
            });
        }

        if (deselectAllTagsBtn) {
            deselectAllTagsBtn.addEventListener('click', function() {
                selectedTagIds.clear();
                includeUntagged = true; // Keep "Untagged" selected
                renderTagFilter();
                applyTagFilter();
            });
        }

        // State filter UI event handlers
        const stateFilterToggle = document.getElementById('stateFilterToggle');
        const stateFilterDropdown = document.getElementById('stateFilterDropdown');
        const selectAllStatesBtn = document.getElementById('selectAllStatesBtn');
        const deselectAllStatesBtn = document.getElementById('deselectAllStatesBtn');

        if (stateFilterToggle && stateFilterDropdown) {
            stateFilterToggle.addEventListener('click', function() {
                const isActive = stateFilterDropdown.classList.contains('active');
                if (isActive) {
                    stateFilterDropdown.classList.remove('active');
                    stateFilterToggle.classList.remove('active');
                } else {
                    stateFilterDropdown.classList.add('active');
                    stateFilterToggle.classList.add('active');
                }
            });
        }

        if (selectAllStatesBtn) {
            selectAllStatesBtn.addEventListener('click', function() {
                selectedStates = new Set(allStates.map(s => s.value));
                renderStateFilter();
                applyStateFilter();
            });
        }

        if (deselectAllStatesBtn) {
            deselectAllStatesBtn.addEventListener('click', function() {
                selectedStates.clear();
                renderStateFilter();
                applyStateFilter();
            });
        }

        async function displayRecipes(recipes) {
            // Reset expanded state when reloading
            expandedRecipeId = null;
            
            if (recipes.length === 0) {
                viewEmptyState.style.display = 'block';
                recipesTableContainer.style.display = 'none';
                recipeCount.style.display = 'none';
                document.getElementById('paginationTop').style.display = 'none';
                document.getElementById('paginationBottom').style.display = 'none';
                return;
            }

            // Calculate pagination
            const totalPages = Math.max(1, Math.ceil(recipes.length / pageSize));
            if (currentPage > totalPages) {
                currentPage = totalPages;
            }
            
            const startIndex = (currentPage - 1) * pageSize;
            const endIndex = Math.min(startIndex + pageSize, recipes.length);
            const pageRecipes = recipes.slice(startIndex, endIndex);

            recipeCount.textContent = `${recipes.length} Recipe${recipes.length !== 1 ? 's' : ''}`;
            recipeCount.style.display = 'block';

            // Update pagination UI
            updatePaginationUI(recipes.length, totalPages);

            recipesTableBody.innerHTML = '';
            
            // First, render all rows with basic thumbnails
            const recipeRows = new Map();
            pageRecipes.forEach((recipe, index) => {
                // Update count to reflect actual position in full list
                recipe.count = startIndex + index + 1;
                // Main row
                const row = document.createElement('tr');
                row.className = 'expandable';
                row.setAttribute('data-recipe-id', recipe.id || '');
                const rotation = recipe.rotation !== undefined ? recipe.rotation : 0;
                
                // Placeholder thumbnail - will be updated after fetching details
                const thumbnail = recipe.id
                    ? `<div class="thumbnail-placeholder" data-recipe-id="${recipe.id}" style="display: flex; flex-direction: column; align-items: center; gap: 8px; min-height: 100px;"><div style="width: 80px; height: 80px; display: flex; align-items: center; justify-content: center; background: #f5f5f5; border-radius: 4px;"><span style="color: #999; font-size: 0.8em;">Loading...</span></div></div>`
                    : '<span style="color: #ccc;">—</span>';
                
                recipeRows.set(recipe.id, { row, recipe });
                
                // Format state with emoji and badge
                const state = recipe.state || 'not_started';
                const stateInfo = getStateInfo(state);
                const stateBadge = `<span class="state-badge state-${state}">${stateInfo.emoji} ${stateInfo.label}</span>`;
                
                row.innerHTML = `
                    <td class="count-column">${recipe.count}</td>
                    <td class="thumbnail-column">${thumbnail}</td>
                    <td class="timestamp-column">${formatTimestamp(recipe.upload_timestamp)}</td>
                    <td class="filename-column">${escapeHtml(recipe.title || recipe.pdf_filename || 'Unknown')}</td>
                    <td class="state-column">${stateBadge}</td>
                    <td class="edit-column"><span class="edit-icon" data-recipe-id="${recipe.id || ''}" title="Edit recipe">✏️</span></td>
                    <td class="admin-column"><span class="admin-gear-icon" data-recipe-id="${recipe.id || ''}">⚙️</span></td>
                `;
                row.setAttribute('data-pdf-filename', recipe.pdf_filename || '');
                recipesTableBody.appendChild(row);

                // Expandable content row
                const expandRow = document.createElement('tr');
                expandRow.className = 'expandable-row-content';
                expandRow.setAttribute('data-recipe-id', recipe.id || '');
                const expandCell = document.createElement('td');
                expandCell.colSpan = 7; // Count, Thumbnail, Timestamp, Filename, State, Edit, Admin
                expandCell.innerHTML = '<div class="detail-grid"><div class="detail-label">Loading...</div><div class="detail-value"></div></div>';
                expandRow.appendChild(expandCell);
                recipesTableBody.appendChild(expandRow);

                // Add click handler to gear icon only
                const gearIcon = row.querySelector('.admin-gear-icon');
                if (gearIcon) {
                    gearIcon.addEventListener('click', function(e) {
                        e.stopPropagation();
                        toggleRowExpansion(recipe.id);
                    });
                }

                // Add click handler to edit icon
                const editIcon = row.querySelector('.edit-icon');
                if (editIcon) {
                    editIcon.addEventListener('click', function(e) {
                        e.stopPropagation();
                        openEditModal(recipe.id);
                    });
                }

            });

            // Now fetch all recipe details in parallel and update thumbnails
            const recipesWithIds = pageRecipes.filter(r => r.id);
            if (recipesWithIds.length > 0) {
                try {
                    const recipeDetailsPromises = recipesWithIds.map(recipe => 
                        fetch(`/api/recipe/${recipe.id}`).then(r => r.json()).catch(err => {
                            console.error(`Error fetching recipe ${recipe.id}:`, err);
                            return null;
                        })
                    );
                    
                    const recipeDetails = await Promise.all(recipeDetailsPromises);
                    
                    // Update thumbnails for each recipe
                    recipeDetails.forEach((recipeData, index) => {
                        if (!recipeData) return;
                        
                        const recipe = recipesWithIds[index];
                        const placeholder = document.querySelector(`.thumbnail-placeholder[data-recipe-id="${recipe.id}"]`);
                        if (!placeholder) return;
                        
                        const thumbnails = [];
                        
                        // Add recipe image (page 1) if it exists
                        if (recipeData.pages && recipeData.pages.length > 0) {
                            const page1 = recipeData.pages[0];
                            const page1Rotation = page1.rotation || 0;
                            thumbnails.push({
                                type: 'recipe',
                                url: `/api/recipe/${recipe.id}/page/${page1.pdf_page_number}/thumbnail`,
                                rotation: page1Rotation,
                                label: 'Recipe Images',
                                pageNumber: page1.pdf_page_number
                            });
                        }
                        
                        // Add dish image (first one) if it exists
                        if (recipeData.dish_images && recipeData.dish_images.length > 0) {
                            const dish1 = recipeData.dish_images[0];
                            const dish1Rotation = dish1.rotation || 0;
                            thumbnails.push({
                                type: 'dish',
                                url: `/api/recipe/${recipe.id}/dish/${dish1.image_number}/thumbnail`,
                                rotation: dish1Rotation,
                                label: 'Dish Images',
                                dishNumber: dish1.image_number
                            });
                        }
                        
                        if (thumbnails.length > 0) {
                            let thumbnailHtml = '<div style="display: flex; flex-direction: column; align-items: center; gap: 8px;">';
                            thumbnails.forEach(thumb => {
                                thumbnailHtml += `
                                    <div class="thumbnail-container" style="display: flex; flex-direction: column; align-items: center;">
                                        <div style="width: 80px; height: 80px; display: flex; align-items: center; justify-content: center; overflow: hidden;">
                                            <img src="${thumb.url}" alt="${thumb.label} thumbnail" class="thumbnail-img" data-recipe-id="${recipe.id}" data-image-type="${thumb.type}" data-page-number="${thumb.pageNumber || ''}" data-dish-number="${thumb.dishNumber || ''}" style="max-width: 80px; max-height: 80px; width: auto; height: auto; object-fit: contain; transform: rotate(${thumb.rotation}deg); cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; border-radius: 4px; border: 1px solid #e0e0e0;" onmouseover="this.style.boxShadow='0 4px 8px rgba(0,0,0,0.2)';" onmouseout="this.style.boxShadow='';">
                                        </div>
                                        <span class="thumbnail-label" style="font-size: 0.6em; color: #666; margin-top: 2px;">${thumb.label}</span>
                                    </div>
                                `;
                            });
                            thumbnailHtml += '</div>';
                            placeholder.outerHTML = thumbnailHtml;
                        } else {
                            placeholder.outerHTML = '<span style="color: #ccc;">—</span>';
                        }
                    });
                } catch (error) {
                    console.error('Error updating thumbnails:', error);
                }
            }

            // Add click handlers and error handlers for thumbnails
            document.querySelectorAll('.thumbnail-img').forEach(thumbnail => {
                thumbnail.addEventListener('click', function(e) {
                    e.stopPropagation();
                    const recipeId = this.getAttribute('data-recipe-id');
                    const imageType = this.getAttribute('data-image-type');
                    const pageNumber = this.getAttribute('data-page-number');
                    const dishNumber = this.getAttribute('data-dish-number');
                    
                    if (recipeId) {
                        if (imageType === 'recipe' && pageNumber !== null && pageNumber !== '') {
                            showImagePreview(recipeId, 'page', parseInt(pageNumber, 10));
                        } else if (imageType === 'dish' && dishNumber !== null && dishNumber !== '') {
                            showImagePreview(recipeId, 'dish', null, parseInt(dishNumber, 10));
                        } else {
                            showImagePreview(recipeId);
                        }
                    }
                });
                thumbnail.addEventListener('error', function() {
                    const recipeId = this.getAttribute('data-recipe-id');
                    console.error('Failed to load thumbnail for recipe', recipeId);
                    this.onerror = null;
                    // Hide the thumbnail and its label
                    const container = this.closest('.thumbnail-container');
                    if (container) {
                        // Hide the entire container (image + label)
                        container.style.display = 'none';
                    } else {
                        this.style.display = 'none';
                        // Also hide the label if it exists
                        const label = this.nextElementSibling;
                        if (label && label.classList && label.classList.contains('thumbnail-label')) {
                            label.style.display = 'none';
                        }
                    }
                });
            });


            recipesTableContainer.style.display = 'block';
            viewEmptyState.style.display = 'none';
        }

        function updatePaginationUI(totalItems, totalPages) {
            // Show pagination controls
            document.getElementById('paginationTop').style.display = 'flex';
            document.getElementById('paginationBottom').style.display = 'flex';
            
            // Update page size selects
            document.getElementById('pageSizeSelect').value = pageSize;
            document.getElementById('pageSizeSelectBottom').value = pageSize;
            
            // Update pagination info
            const startItem = totalItems === 0 ? 0 : (currentPage - 1) * pageSize + 1;
            const endItem = Math.min(currentPage * pageSize, totalItems);
            const infoText = `Showing ${startItem}-${endItem} of ${totalItems}`;
            document.getElementById('paginationInfoTop').textContent = infoText;
            document.getElementById('paginationInfoBottom').textContent = infoText;
            
            // Update page jump inputs and total pages
            document.getElementById('pageJumpInput').value = currentPage;
            document.getElementById('pageJumpInput').max = totalPages;
            document.getElementById('pageJumpInputBottom').value = currentPage;
            document.getElementById('pageJumpInputBottom').max = totalPages;
            document.getElementById('totalPagesSpan').textContent = `of ${totalPages}`;
            document.getElementById('totalPagesSpanBottom').textContent = `of ${totalPages}`;
            
            // Update button states
            const isFirstPage = currentPage === 1;
            const isLastPage = currentPage === totalPages;
            
            // Top buttons
            document.getElementById('firstPageBtn').disabled = isFirstPage;
            document.getElementById('prevPageBtn').disabled = isFirstPage;
            document.getElementById('nextPageBtn').disabled = isLastPage;
            document.getElementById('lastPageBtn').disabled = isLastPage;
            
            // Bottom buttons
            document.getElementById('firstPageBtnBottom').disabled = isFirstPage;
            document.getElementById('prevPageBtnBottom').disabled = isFirstPage;
            document.getElementById('nextPageBtnBottom').disabled = isLastPage;
            document.getElementById('lastPageBtnBottom').disabled = isLastPage;
        }

        function goToPage(page) {
            const totalPages = Math.max(1, Math.ceil(filteredRecipes.length / pageSize));
            if (page >= 1 && page <= totalPages) {
                currentPage = page;
                displayRecipes(filteredRecipes);
                // Scroll to top of table
                document.getElementById('recipesTableContainer').scrollIntoView({ behavior: 'smooth', block: 'start' });
                saveViewState();
            }
        }

        function changePageSize(newSize) {
            pageSize = parseInt(newSize, 10);
            const totalPages = Math.max(1, Math.ceil(filteredRecipes.length / pageSize));
            if (currentPage > totalPages) {
                currentPage = totalPages;
            }
            displayRecipes(filteredRecipes);
            saveViewState();
        }

        // Pagination event handlers
        document.getElementById('firstPageBtn').addEventListener('click', () => goToPage(1));
        document.getElementById('prevPageBtn').addEventListener('click', () => goToPage(currentPage - 1));
        document.getElementById('nextPageBtn').addEventListener('click', () => goToPage(currentPage + 1));
        document.getElementById('lastPageBtn').addEventListener('click', () => {
            const totalPages = Math.max(1, Math.ceil(filteredRecipes.length / pageSize));
            goToPage(totalPages);
        });

        document.getElementById('firstPageBtnBottom').addEventListener('click', () => goToPage(1));
        document.getElementById('prevPageBtnBottom').addEventListener('click', () => goToPage(currentPage - 1));
        document.getElementById('nextPageBtnBottom').addEventListener('click', () => goToPage(currentPage + 1));
        document.getElementById('lastPageBtnBottom').addEventListener('click', () => {
            const totalPages = Math.max(1, Math.ceil(filteredRecipes.length / pageSize));
            goToPage(totalPages);
        });

        document.getElementById('pageSizeSelect').addEventListener('change', function() {
            changePageSize(this.value);
        });

        document.getElementById('pageSizeSelectBottom').addEventListener('change', function() {
            changePageSize(this.value);
        });

        document.getElementById('pageJumpBtn').addEventListener('click', function() {
            const page = parseInt(document.getElementById('pageJumpInput').value, 10);
            goToPage(page);
        });

        document.getElementById('pageJumpBtnBottom').addEventListener('click', function() {
            const page = parseInt(document.getElementById('pageJumpInputBottom').value, 10);
            goToPage(page);
        });

        // Allow Enter key in page jump inputs
        document.getElementById('pageJumpInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const page = parseInt(this.value, 10);
                goToPage(page);
            }
        });

        document.getElementById('pageJumpInputBottom').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const page = parseInt(this.value, 10);
                goToPage(page);
            }
        });

        function formatTimestamp(timestamp) {
            if (!timestamp) return 'Unknown';
            try {
                const date = new Date(timestamp);
                return date.toLocaleString();
            } catch (e) {
                return timestamp;
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function renderTags(tags) {
            if (!tags || tags.length === 0) {
                return '';
            }
            return tags.map(tag => `
                <span class="tag-chip" data-tag-id="${tag.id}" data-recipe-tag-id="${tag.recipe_tag_id}">
                    ${escapeHtml(tag.tag_name)}
                    <button class="tag-remove" onclick="removeTag(${tag.recipe_tag_id}, ${tag.id})" title="Remove tag">×</button>
                </span>
            `).join('');
        }

        async function addTag(recipeId, tagName) {
            if (!tagName || !tagName.trim()) {
                return;
            }

            const tagInput = document.getElementById(`tag-input-${recipeId}`);
            const tagsContainer = document.getElementById(`tags-container-${recipeId}`);
            
            // Disable input while adding
            tagInput.disabled = true;
            tagInput.value = '';

            try {
                const response = await fetch(`/api/recipe/${recipeId}/tags`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ tag_name: tagName.trim() })
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
                    throw new Error(errorData.error || 'Failed to add tag');
                }

                const result = await response.json();
                
                // Add the new tag chip before the input wrapper
                const inputWrapper = tagsContainer.querySelector('.tag-input-wrapper');
                const newTagChip = document.createElement('span');
                newTagChip.className = 'tag-chip';
                newTagChip.setAttribute('data-tag-id', result.tag.id);
                newTagChip.setAttribute('data-recipe-tag-id', result.tag.recipe_tag_id);
                newTagChip.innerHTML = `
                    ${escapeHtml(result.tag.tag_name)}
                    <button class="tag-remove" onclick="removeTag(${result.tag.recipe_tag_id}, ${result.tag.id})" title="Remove tag">×</button>
                `;
                tagsContainer.insertBefore(newTagChip, inputWrapper);
            } catch (error) {
                console.error('Error adding tag:', error);
                alert('Failed to add tag: ' + error.message);
                tagInput.value = tagName; // Restore the value on error
            } finally {
                tagInput.disabled = false;
                tagInput.focus();
            }
        }

        async function removeTag(recipeTagId, tagId) {
            const tagChip = document.querySelector(`.tag-chip[data-recipe-tag-id="${recipeTagId}"]`);
            if (!tagChip) return;

            const recipeId = tagChip.closest('.tags-container').getAttribute('data-recipe-id');
            
            // Remove from UI immediately for better UX
            tagChip.style.opacity = '0.5';
            tagChip.style.pointerEvents = 'none';

            try {
                const response = await fetch(`/api/recipe/${recipeId}/tags/${recipeTagId}`, {
                    method: 'DELETE'
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
                    throw new Error(errorData.error || 'Failed to remove tag');
                }

                // Remove from DOM
                tagChip.remove();
            } catch (error) {
                console.error('Error removing tag:', error);
                alert('Failed to remove tag: ' + error.message);
                // Restore UI on error
                tagChip.style.opacity = '1';
                tagChip.style.pointerEvents = 'auto';
            }
        }

        function getStateInfo(state) {
            const stateMap = {
                'not_started': { emoji: '⏳', label: 'Not Started' },
                'partially_complete': { emoji: '🔄', label: 'In Progress' },
                'complete': { emoji: '✅', label: 'Complete' },
                'broken': { emoji: '❌', label: 'Broken' },
                'duplicate': { emoji: '📋', label: 'Duplicate' }
            };
            return stateMap[state] || { emoji: '❓', label: 'Unknown' };
        }

        let expandedRecipeId = null;

        async function toggleRowExpansion(recipeId) {
            const expandRow = document.querySelector(`.expandable-row-content[data-recipe-id="${recipeId}"]`);
            const mainRow = document.querySelector(`tr.expandable[data-recipe-id="${recipeId}"]`);
            
            if (!expandRow || !mainRow) return;

            // If clicking the same row, collapse it
            if (expandedRecipeId === recipeId) {
                expandRow.classList.remove('expanded');
                mainRow.classList.remove('expanded');
                expandedRecipeId = null;
                return;
            }

            // Collapse previously expanded row
            if (expandedRecipeId !== null) {
                const prevExpandRow = document.querySelector(`.expandable-row-content[data-recipe-id="${expandedRecipeId}"]`);
                const prevMainRow = document.querySelector(`tr.expandable[data-recipe-id="${expandedRecipeId}"]`);
                if (prevExpandRow) prevExpandRow.classList.remove('expanded');
                if (prevMainRow) prevMainRow.classList.remove('expanded');
            }

            // Expand new row
            expandRow.classList.add('expanded');
            mainRow.classList.add('expanded');
            expandedRecipeId = recipeId;

            // Load recipe details if not already loaded
            const detailGrid = expandRow.querySelector('.detail-grid');
            if (detailGrid && detailGrid.innerHTML.includes('Loading...')) {
                try {
                    const response = await fetch(`/api/recipe/${recipeId}`);
                    
                    if (!response.ok) {
                        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
                        throw new Error(errorData.error || 'Failed to load recipe details');
                    }
                    
                    const data = await response.json();

                    // Format the details with editable fields
                    const stateOptions = ['not_started', 'partially_complete', 'complete', 'broken', 'duplicate'];
                    const stateOptionLabels = {
                        'not_started': 'Not Started',
                        'partially_complete': 'In Progress',
                        'complete': 'Complete',
                        'broken': 'Broken',
                        'duplicate': 'Duplicate'
                    };
                    detailGrid.innerHTML = `
                        <div class="detail-label">Recipe Filename:</div>
                        <div class="detail-value">${escapeHtml(data.pdf_filename || 'N/A')}</div>
                        
                        <div class="detail-label">Upload Timestamp:</div>
                        <div class="detail-value">${formatTimestamp(data.pdf_upload_timestamp)}</div>
                        
                        <div class="detail-label">Original PDF SHA256:</div>
                        <div class="detail-value">${data.original_pdf_sha256 || '<span class="empty">Not available</span>'}</div>
                        
                        <div class="detail-label">Original PDF Size:</div>
                        <div class="detail-value">${formatFileSize(data.original_pdf_size)}</div>
                        
                        <div class="detail-label">State:</div>
                        <div class="detail-value">
                            <select class="editable-field" data-field="state" style="width: 100%; padding: 5px; border: 1px solid #ddd; border-radius: 4px;">
                                ${stateOptions.map(state => `<option value="${state}" ${data.state === state ? 'selected' : ''}>${stateOptionLabels[state]}</option>`).join('')}
                            </select>
                        </div>
                        
                        <div class="detail-label">Title:</div>
                        <div class="detail-value">
                            <input type="text" class="editable-field" data-field="title" value="${escapeHtml(data.title || '')}" placeholder="Not set" style="width: 100%; padding: 5px; border: 1px solid #ddd; border-radius: 4px;">
                        </div>
                        
                        <div class="detail-label">Description:</div>
                        <div class="detail-value">
                            <textarea class="editable-field" data-field="description" placeholder="Not set" style="width: 100%; padding: 5px; border: 1px solid #ddd; border-radius: 4px; min-height: 60px; resize: vertical;">${escapeHtml(data.description || '')}</textarea>
                        </div>
                        
                        <div class="detail-label">Year:</div>
                        <div class="detail-value">
                            <input type="number" class="editable-field" data-field="year" value="${data.year || ''}" placeholder="Not set" style="width: 100%; padding: 5px; border: 1px solid #ddd; border-radius: 4px;">
                        </div>
                        
                        <div class="detail-label">Author:</div>
                        <div class="detail-value">
                            <input type="text" class="editable-field" data-field="author" value="${escapeHtml(data.author || '')}" placeholder="Not set" style="width: 100%; padding: 5px; border: 1px solid #ddd; border-radius: 4px;">
                        </div>
                        
                        <div class="detail-label">Ingredients:</div>
                        <div class="detail-value">
                            <textarea class="editable-field" data-field="ingredients" placeholder="Not set" style="width: 100%; padding: 5px; border: 1px solid #ddd; border-radius: 4px; min-height: 80px; resize: vertical;">${escapeHtml(data.ingredients || '')}</textarea>
                        </div>
                        
                        <div class="detail-label">Recipe:</div>
                        <div class="detail-value">
                            <textarea class="editable-field" data-field="recipe" placeholder="Not set" style="width: 100%; padding: 5px; border: 1px solid #ddd; border-radius: 4px; min-height: 80px; resize: vertical;">${escapeHtml(data.recipe || '')}</textarea>
                        </div>
                        
                        <div class="detail-label">Cook Time:</div>
                        <div class="detail-value">
                            <input type="text" class="editable-field" data-field="cook_time" value="${escapeHtml(data.cook_time || '')}" placeholder="Not set" style="width: 100%; padding: 5px; border: 1px solid #ddd; border-radius: 4px;">
                        </div>
                        
                        <div class="detail-label">Notes:</div>
                        <div class="detail-value">
                            <textarea class="editable-field" data-field="notes" placeholder="Not set" style="width: 100%; padding: 5px; border: 1px solid #ddd; border-radius: 4px; min-height: 60px; resize: vertical;">${escapeHtml(data.notes || '')}</textarea>
                        </div>
                        
                        <div class="detail-label">Tags:</div>
                        <div class="detail-value">
                            <div class="tags-container" id="tags-container-${recipeId}" data-recipe-id="${recipeId}">
                                ${renderTags(data.tags || [])}
                                <div class="tag-input-wrapper">
                                    <input type="text" class="tag-input" id="tag-input-${recipeId}" placeholder="Type a tag and press Enter..." data-recipe-id="${recipeId}">
                                </div>
                            </div>
                        </div>
                        
                        <div class="detail-label">Total Pages:</div>
                        <div class="detail-value">${data.total_pages || 0}</div>
                        
                        <div class="detail-label">Total Dish Images:</div>
                        <div class="detail-value">${data.total_dish_images || 0}</div>
                        
                        <div style="grid-column: 1 / -1; margin-top: 20px; margin-bottom: 10px;">
                            <button id="save-recipe-btn-${recipeId}" class="save-recipe-btn" data-recipe-id="${recipeId}" type="button" style="background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 14px; transition: background 0.2s; position: relative; z-index: 10;" onmouseover="this.style.background='#5568d3';" onmouseout="this.style.background='#667eea';">
                                💾 Save Changes
                            </button>
                            <span id="save-status-${recipeId}" style="margin-left: 15px; color: #666;"></span>
                        </div>
                    `;
                    
                    // Add sub-expandable section for recipe images (PDF pages)
                    if (data.pages !== undefined) {
                        const pageCount = data.pages ? data.pages.length : 0;
                        let pagesHtml = `
                            <div class="sub-expandable-section">
                                <div class="sub-expandable-header" data-section="recipe-images-${recipeId}">
                                    <span style="font-weight: 600; color: #667eea;">📄 Recipe Images (PDF Pages) - ${pageCount} page(s)</span>
                                    <span class="sub-expandable-icon">▶</span>
                                </div>
                                <div class="sub-expandable-content" id="recipe-images-${recipeId}">
                                    <div class="sub-expandable-grid">
                        `;
                        if (pageCount === 0) {
                            pagesHtml += `
                                <div class="detail-label" style="grid-column: 1 / -1; color: #999; font-style: italic;">No recipe images available</div>
                            `;
                        } else {
                            data.pages.forEach((page, index) => {
                            const pageNum = page.pdf_page_number + 1; // Convert 0-indexed to 1-indexed for display
                            pagesHtml += `
                                <div class="detail-label" style="grid-column: 1 / -1; margin-top: ${index > 0 ? '15px' : '0'}; font-weight: 600; color: #667eea; border-top: ${index > 0 ? '1px solid #e0e0e0' : 'none'}; padding-top: ${index > 0 ? '10px' : '0'}; display: flex; align-items: center; gap: 15px;">
                                    <span>Page ${pageNum}:</span>
                                    <div style="width: 100px; height: 100px; display: flex; align-items: center; justify-content: center; overflow: hidden;">
                                        <img src="/api/recipe/${recipeId}/page/${page.pdf_page_number}/thumbnail" alt="Page ${pageNum} thumbnail" class="thumbnail-clickable ${page.unneeded ? 'image-unneeded' : ''}" data-recipe-id="${recipeId}" data-image-type="page" data-page-number="${page.pdf_page_number}" style="max-width: 100px; max-height: 100px; width: auto; height: auto; object-fit: contain; border-radius: 4px; border: 1px solid #e0e0e0; transform: rotate(${page.rotation}deg); cursor: pointer; transition: transform 0.2s, box-shadow 0.2s;" onerror="this.style.display='none';" onmouseover="this.style.boxShadow='0 4px 8px rgba(0,0,0,0.2)';" onmouseout="this.style.boxShadow='';">
                                    </div>
                                </div>
                                <div class="detail-label">Rotation:</div>
                                <div class="detail-value">${page.rotation}°</div>
                                <div class="detail-label">Unneeded:</div>
                                <div class="detail-value">
                                    <input type="checkbox" class="admin-unneeded-checkbox" data-recipe-id="${recipeId}" data-page-number="${page.pdf_page_number}" ${page.unneeded ? 'checked' : ''} title="Mark image as unneeded">
                                </div>
                                <div class="detail-label">Cropped Image SHA256:</div>
                                <div class="detail-value">${page.cropped_image_sha256 || '<span class="empty">Not available</span>'}</div>
                                <div class="detail-label">Cropped Image Size:</div>
                                <div class="detail-value">${formatFileSize(page.cropped_image_size)}</div>
                                <div class="detail-label">Medium Image SHA256:</div>
                                <div class="detail-value">${page.medium_image_sha256 || '<span class="empty">Not available</span>'}</div>
                                <div class="detail-label">Medium Image Size:</div>
                                <div class="detail-value">${formatFileSize(page.medium_image_size)}</div>
                                <div class="detail-label">Thumbnail SHA256:</div>
                                <div class="detail-value">${page.thumbnail_sha256 || '<span class="empty">Not available</span>'}</div>
                                <div class="detail-label">Thumbnail Size:</div>
                                <div class="detail-value">${formatFileSize(page.thumbnail_size)}</div>
                            `;
                            });
                        }
                        pagesHtml += `
                                    </div>
                                </div>
                            </div>
                        `;
                        detailGrid.innerHTML += pagesHtml;
                    }
                    
                    // Add sub-expandable section for dish images
                    if (data.dish_images !== undefined) {
                        const dishImageCount = data.dish_images ? data.dish_images.length : 0;
                        let dishImagesHtml = `
                            <div class="sub-expandable-section">
                                <div class="sub-expandable-header" data-section="dish-images-${recipeId}">
                                    <span style="font-weight: 600; color: #667eea;">🍽️ Dish Images - ${dishImageCount} image(s)</span>
                                    <span class="sub-expandable-icon">▶</span>
                                </div>
                                <div class="sub-expandable-content" id="dish-images-${recipeId}">
                                    <div class="sub-expandable-grid">
                        `;
                        if (dishImageCount === 0) {
                            dishImagesHtml += `
                                <div class="detail-label" style="grid-column: 1 / -1; color: #999; font-style: italic;">No dish images available</div>
                            `;
                        } else {
                            data.dish_images.forEach((dishImg, index) => {
                            dishImagesHtml += `
                                <div class="detail-label" style="grid-column: 1 / -1; margin-top: ${index > 0 ? '15px' : '0'}; font-weight: 600; color: #667eea; border-top: ${index > 0 ? '1px solid #e0e0e0' : 'none'}; padding-top: ${index > 0 ? '10px' : '0'}; display: flex; align-items: center; gap: 15px;">
                                    <span>Dish Image ${dishImg.image_number}:</span>
                                    <div style="width: 100px; height: 100px; display: flex; align-items: center; justify-content: center; overflow: hidden;">
                                        <img src="/api/recipe/${recipeId}/dish/${dishImg.image_number}/thumbnail" alt="Dish Image ${dishImg.image_number} thumbnail" class="thumbnail-clickable" data-recipe-id="${recipeId}" data-image-type="dish" data-dish-number="${dishImg.image_number}" style="max-width: 100px; max-height: 100px; width: auto; height: auto; object-fit: contain; border-radius: 4px; border: 1px solid #e0e0e0; transform: rotate(${dishImg.rotation}deg); cursor: pointer; transition: transform 0.2s, box-shadow 0.2s;" onerror="this.style.display='none';" onmouseover="this.style.boxShadow='0 4px 8px rgba(0,0,0,0.2)';" onmouseout="this.style.boxShadow='';">
                                    </div>
                                </div>
                                <div class="detail-label">Rotation:</div>
                                <div class="detail-value">${dishImg.rotation}°</div>
                                <div class="detail-label">Image SHA256:</div>
                                <div class="detail-value">${dishImg.image_sha256 || '<span class="empty">Not available</span>'}</div>
                                <div class="detail-label">Image Size:</div>
                                <div class="detail-value">${formatFileSize(dishImg.image_size)}</div>
                                <div class="detail-label">Medium Image SHA256:</div>
                                <div class="detail-value">${dishImg.medium_image_sha256 || '<span class="empty">Not available</span>'}</div>
                                <div class="detail-label">Medium Image Size:</div>
                                <div class="detail-value">${formatFileSize(dishImg.medium_image_size)}</div>
                                <div class="detail-label">Thumbnail SHA256:</div>
                                <div class="detail-value">${dishImg.thumbnail_sha256 || '<span class="empty">Not available</span>'}</div>
                                <div class="detail-label">Thumbnail Size:</div>
                                <div class="detail-value">${formatFileSize(dishImg.thumbnail_size)}</div>
                            `;
                            });
                        }
                        dishImagesHtml += `
                                    </div>
                                </div>
                            </div>
                        `;
                        detailGrid.innerHTML += dishImagesHtml;
                    }
                    
                    // Add click handlers for sub-expandable sections
                    detailGrid.querySelectorAll('.sub-expandable-header').forEach(header => {
                        header.addEventListener('click', function() {
                            const sectionId = this.getAttribute('data-section');
                            const content = document.getElementById(sectionId);
                            if (content) {
                                const isExpanded = content.classList.contains('expanded');
                                if (isExpanded) {
                                    content.classList.remove('expanded');
                                    this.classList.remove('expanded');
                                } else {
                                    content.classList.add('expanded');
                                    this.classList.add('expanded');
                                }
                            }
                        });
                    });
                    
                    // Add click handlers for thumbnail images
                    detailGrid.querySelectorAll('.thumbnail-clickable').forEach(thumbnail => {
                        thumbnail.addEventListener('click', function(e) {
                            e.stopPropagation();
                            const recipeId = this.getAttribute('data-recipe-id');
                            const imageType = this.getAttribute('data-image-type');
                            const pageNumber = this.getAttribute('data-page-number');
                            const dishNumber = this.getAttribute('data-dish-number');
                            
                            if (recipeId) {
                                if (imageType === 'page' && pageNumber !== null) {
                                    showImagePreview(recipeId, 'page', parseInt(pageNumber, 10));
                                } else if (imageType === 'dish' && dishNumber !== null) {
                                    showImagePreview(recipeId, 'dish', null, parseInt(dishNumber, 10));
                                } else {
                                    showImagePreview(recipeId);
                                }
                            }
                        });
                    });
                    
                    // Add event handlers for admin unneeded checkboxes
                    detailGrid.querySelectorAll('.admin-unneeded-checkbox').forEach(checkbox => {
                        checkbox.addEventListener('change', async function(e) {
                            e.stopPropagation();
                            const recipeId = parseInt(this.getAttribute('data-recipe-id'), 10);
                            const pageNumber = parseInt(this.getAttribute('data-page-number'), 10);
                            const unneeded = this.checked;
                            
                            try {
                                const response = await fetch(`/api/recipe/${recipeId}/page/${pageNumber}/unneeded`, {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json',
                                    },
                                    body: JSON.stringify({ unneeded: unneeded })
                                });

                                if (!response.ok) {
                                    const data = await response.json();
                                    throw new Error(data.error || 'Failed to update unneeded status');
                                }

                                // Update the thumbnail image style
                                const thumbnail = detailGrid.querySelector(`.thumbnail-clickable[data-page-number="${pageNumber}"]`);
                                if (thumbnail) {
                                    if (unneeded) {
                                        thumbnail.classList.add('image-unneeded');
                                    } else {
                                        thumbnail.classList.remove('image-unneeded');
                                    }
                                }
                            } catch (error) {
                                console.error('Error updating unneeded status:', error);
                                // Revert checkbox
                                this.checked = !unneeded;
                            }
                        });
                    });
                    
                    // Add event handler for tag input
                    const tagInput = document.getElementById(`tag-input-${recipeId}`);
                    if (tagInput) {
                        tagInput.addEventListener('keydown', function(e) {
                            if (e.key === 'Enter') {
                                e.preventDefault();
                                const tagName = this.value.trim();
                                if (tagName) {
                                    addTag(recipeId, tagName);
                                }
                            }
                        });
                    }
                } catch (error) {
                    console.error('Error loading recipe details:', error);
                    detailGrid.innerHTML = `
                        <div class="detail-label">Error:</div>
                        <div class="detail-value" style="color: #c33;">${escapeHtml(error.message)}</div>
                        <div class="detail-label">Note:</div>
                        <div class="detail-value">This recipe may not have RecipeImage entries. Try re-uploading the PDF.</div>
                    `;
                }
            }
        }
        
        async function saveRecipeChanges(recipeId) {
            console.log('saveRecipeChanges called for recipe', recipeId);
            const saveBtn = document.getElementById(`save-recipe-btn-${recipeId}`);
            const statusSpan = document.getElementById(`save-status-${recipeId}`);
            
            if (!saveBtn) {
                console.error('Save button not found for recipe', recipeId);
                return;
            }
            if (!statusSpan) {
                console.error('Status span not found for recipe', recipeId);
                return;
            }
            
            // Collect all field values
            const fields = {};
            const editableFields = document.querySelectorAll(`.expandable-row-content[data-recipe-id="${recipeId}"] .editable-field`);
            
            console.log('Found', editableFields.length, 'editable fields');
            
            editableFields.forEach(field => {
                const fieldName = field.getAttribute('data-field');
                if (fieldName) {
                    if (field.tagName === 'TEXTAREA' || field.tagName === 'INPUT') {
                        fields[fieldName] = field.value || null;
                    } else if (field.tagName === 'SELECT') {
                        fields[fieldName] = field.value;
                    }
                    console.log('Field', fieldName, '=', fields[fieldName]);
                }
            });
            
            // Convert year to number if provided
            if (fields.year !== null && fields.year !== undefined && fields.year !== '') {
                const yearNum = parseInt(fields.year, 10);
                if (!isNaN(yearNum)) {
                    fields.year = yearNum;
                } else {
                    fields.year = null;
                }
            } else {
                fields.year = null;
            }
            
            console.log('Saving fields:', fields);
            
            // Show saving status
            saveBtn.disabled = true;
            saveBtn.style.opacity = '0.6';
            statusSpan.textContent = 'Saving...';
            statusSpan.style.color = '#666';
            
            try {
                const response = await fetch(`/api/recipe/${recipeId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(fields)
                });
                
                console.log('Response status:', response.status);
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
                    console.error('Error response:', errorData);
                    throw new Error(errorData.error || 'Failed to save changes');
                }
                
                const result = await response.json();
                console.log('Save result:', result);
                
                statusSpan.textContent = '✓ Saved successfully';
                statusSpan.style.color = '#28a745';
                
                // Update the main table row with any changed fields
                const mainRow = document.querySelector(`tr.expandable[data-recipe-id="${recipeId}"]`);
                if (mainRow) {
                    // Update title if it changed
                    if (fields.title !== undefined) {
                        const filenameCell = mainRow.querySelector('.filename-column');
                        if (filenameCell) {
                            filenameCell.textContent = fields.title || mainRow.getAttribute('data-pdf-filename') || 'Unknown';
                        }
                    }
                    
                    // Update state badge if it changed
                    if (fields.state !== undefined) {
                        const stateCell = mainRow.querySelector('.state-column');
                        if (stateCell) {
                            const stateInfo = getStateInfo(fields.state);
                            stateCell.innerHTML = `<span class="state-badge state-${fields.state}">${stateInfo.emoji} ${stateInfo.label}</span>`;
                        }
                    }
                }
                
                // Reset status after 3 seconds
                setTimeout(() => {
                    statusSpan.textContent = '';
                }, 3000);
                
            } catch (error) {
                console.error('Save error:', error);
                statusSpan.textContent = '✗ Error: ' + error.message;
                statusSpan.style.color = '#c33';
            } finally {
                saveBtn.disabled = false;
                saveBtn.style.opacity = '1';
            }
        }

        // Image preview functionality
        const imageOverlay = document.getElementById('imageOverlay');
        const previewImage = document.getElementById('previewImage');
        const imageOverlayClose = document.getElementById('imageOverlayClose');
        const imageOverlayTitle = document.getElementById('imageOverlayTitle');
        const rotateClockwise = document.getElementById('rotateClockwise');
        const rotateCounterClockwise = document.getElementById('rotateCounterClockwise');
        const rotationDisplay = document.getElementById('rotationDisplay');
        
        let currentRecipeId = null;
        let currentRotation = 0;
        let currentImageType = null; // 'recipe', 'page', or 'dish'
        let currentPageNumber = null;
        let currentDishNumber = null;
        let currentImageIndex = 0; // Index within current group
        let currentImageGroup = []; // Array of images in current group
        let currentGroupType = null; // 'recipe' or 'dish'
        let imageOverlayZoomed = false;
        let imageOverlayTransform = { x: 0, y: 0, scale: 1 };
        let currentUnneeded = false;

        function showImagePreview(recipeId, imageType = 'recipe', pageNumber = null, dishNumber = null) {
            // Convert recipeId to number for comparison
            const recipeIdNum = parseInt(recipeId, 10);
            currentRecipeId = recipeIdNum;
            currentImageType = imageType;
            currentPageNumber = pageNumber;
            currentDishNumber = dishNumber;
            
            // Reset rotation display while loading
            rotationDisplay.textContent = 'Loading...';
            
            // Load recipe data to get image groups
            fetch(`/api/recipe/${recipeIdNum}`)
                .then(response => response.json())
                .then(data => {
                    // Determine which group we're in and set up navigation
                    if (imageType === 'page' && pageNumber !== null) {
                        currentGroupType = 'recipe';
                        currentImageGroup = data.pages || [];
                        currentImageIndex = currentImageGroup.findIndex(p => p.pdf_page_number === pageNumber);
                        if (currentImageIndex === -1) {
                            // If page not found, default to first page
                            currentImageIndex = 0;
                        }
                    } else if (imageType === 'dish' && dishNumber !== null) {
                        currentGroupType = 'dish';
                        currentImageGroup = data.dish_images || [];
                        currentImageIndex = currentImageGroup.findIndex(d => d.image_number === dishNumber);
                        if (currentImageIndex === -1) {
                            // If dish image not found, default to first dish image
                            currentImageIndex = 0;
                        }
                    } else {
                        // Default to recipe page 1
                        currentGroupType = 'recipe';
                        currentImageGroup = data.pages || [];
                        currentImageIndex = 0;
                    }
                    
                    // Show/hide navigation arrows based on group size
                    updateNavigationArrows();
                    
                    // Load the image
                    loadCurrentImage(data);
                })
                .catch(err => {
                    console.error('Error fetching recipe data:', err);
                    // Fallback to basic image loading
                    loadCurrentImage(null);
                });
        }
        
        function loadCurrentImage(recipeData) {
            const recipeIdNum = currentRecipeId;
            let imageUrl;
            let rotation = 0;
            
            // Update title if recipeData is available
            if (recipeData && recipeData.title) {
                imageOverlayTitle.textContent = recipeData.title;
                imageOverlayTitle.style.display = 'block';
            } else if (recipeData && recipeData.pdf_filename) {
                // Fallback to PDF filename if no title
                imageOverlayTitle.textContent = recipeData.pdf_filename;
                imageOverlayTitle.style.display = 'block';
            } else {
                imageOverlayTitle.textContent = '';
                imageOverlayTitle.style.display = 'none';
            }
            
            console.log('loadCurrentImage called:', {
                currentGroupType,
                currentImageGroupLength: currentImageGroup.length,
                currentImageIndex,
                recipeIdNum
            });
            
            if (currentGroupType === 'recipe' && currentImageGroup.length > 0 && currentImageIndex >= 0 && currentImageIndex < currentImageGroup.length) {
                const page = currentImageGroup[currentImageIndex];
                currentPageNumber = page.pdf_page_number;
                imageUrl = `/api/recipe/${recipeIdNum}/page/${page.pdf_page_number}/image`;
                rotation = page.rotation || 0;
                currentUnneeded = page.unneeded || false;
                console.log('Loading recipe page image:', imageUrl, 'page number:', page.pdf_page_number);
            } else if (currentGroupType === 'dish' && currentImageGroup.length > 0 && currentImageIndex >= 0 && currentImageIndex < currentImageGroup.length) {
                const dishImg = currentImageGroup[currentImageIndex];
                currentDishNumber = dishImg.image_number;
                imageUrl = `/api/recipe/${recipeIdNum}/dish/${dishImg.image_number}/image`;
                rotation = dishImg.rotation || 0;
                currentUnneeded = false; // Dish images don't have unneeded field
                console.log('Loading dish image:', imageUrl, 'dish number:', dishImg.image_number);
            } else {
                // Default to recipe page 1
                imageUrl = `/api/recipe/${recipeIdNum}/image`;
                if (recipeData && recipeData.pages && recipeData.pages.length > 0) {
                    const page = recipeData.pages[0];
                    rotation = page.rotation || 0;
                    currentUnneeded = page.unneeded || false;
                } else {
                    currentUnneeded = false;
                }
                console.log('Loading default recipe image:', imageUrl);
            }
            
            currentRotation = rotation;
            // Reset zoom and position when loading new image
            imageOverlayZoomed = false;
            imageOverlayTransform = { x: 0, y: 0, scale: 1 };
            updateRotationDisplay();
            updateImageOverlayTransform();
            updateUnneededCheckbox();
            updateImageUnneededStyle();
            
            previewImage.onerror = function() {
                this.onerror = null;
                this.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="400"%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dominant-baseline="middle" fill="%23ccc" font-size="20"%3ENo Image Available%3C/text%3E%3C/svg%3E';
                console.error('Failed to load image:', imageUrl);
            };
            previewImage.src = imageUrl;
            imageOverlay.classList.add('active');
        }
        
        function updateNavigationArrows() {
            const leftArrow = document.getElementById('imageNavLeft');
            const rightArrow = document.getElementById('imageNavRight');
            
            if (currentImageGroup.length > 1) {
                // Always show both arrows when there are multiple images (wrapping enabled)
                leftArrow.style.display = 'flex';
                rightArrow.style.display = 'flex';
            } else {
                leftArrow.style.display = 'none';
                rightArrow.style.display = 'none';
            }
        }
        
        function navigateImage(direction) {
            if (currentImageGroup.length <= 1) return;
            
            if (direction === 'next') {
                currentImageIndex = (currentImageIndex + 1) % currentImageGroup.length; // Wrap around
            } else if (direction === 'prev') {
                currentImageIndex = (currentImageIndex - 1 + currentImageGroup.length) % currentImageGroup.length; // Wrap around
            }
            
            // Reload recipe data to get fresh rotation values
            fetch(`/api/recipe/${currentRecipeId}`)
                .then(response => response.json())
                .then(data => {
                    if (currentGroupType === 'recipe') {
                        currentImageGroup = data.pages || [];
                    } else if (currentGroupType === 'dish') {
                        currentImageGroup = data.dish_images || [];
                    }
                    updateNavigationArrows();
                    loadCurrentImage(data);
                })
                .catch(err => {
                    console.error('Error fetching recipe data:', err);
                    updateNavigationArrows();
                    loadCurrentImage(null);
                });
        }

        function updateRotationDisplay() {
            if (rotationDisplay) {
                rotationDisplay.textContent = `${currentRotation}°`;
            }
        }

        function updateImageRotation() {
            if (previewImage) {
                const rotation = currentRotation || 0;
                const scale = imageOverlayTransform.scale;
                const x = imageOverlayTransform.x;
                const y = imageOverlayTransform.y;
                previewImage.style.transform = `translate(${x}px, ${y}px) scale(${scale}) rotate(${rotation}deg)`;
                previewImage.style.transformOrigin = 'center center';
            }
        }

        function updateImageOverlayTransform() {
            updateImageRotation();
            const content = document.querySelector('.image-overlay-content');
            if (content) {
                if (imageOverlayZoomed) {
                    content.classList.add('zoomed');
                    previewImage.classList.add('zoomed');
                } else {
                    content.classList.remove('zoomed');
                    previewImage.classList.remove('zoomed');
                }
            }
        }

        function toggleImageOverlayZoom() {
            imageOverlayZoomed = !imageOverlayZoomed;
            
            if (imageOverlayZoomed) {
                imageOverlayTransform.scale = 2;
            } else {
                imageOverlayTransform.scale = 1;
                imageOverlayTransform.x = 0;
                imageOverlayTransform.y = 0;
            }
            
            updateImageOverlayTransform();
        }

        async function rotateImage(direction) {
            if (!currentRecipeId) return;
            
            // Ensure currentRotation is a number
            currentRotation = parseInt(currentRotation, 10) || 0;
            
            // Calculate new rotation
            if (direction === 'clockwise') {
                currentRotation = (currentRotation + 90) % 360;
            } else {
                currentRotation = (currentRotation - 90 + 360) % 360;
            }
            
            // Update display immediately for responsive UI
            updateRotationDisplay();
            updateImageOverlayTransform();
            
            // Update database
            try {
                const rotationData = { rotation: currentRotation };
                if (currentImageType === 'page' && currentPageNumber !== null) {
                    rotationData.image_type = 'page';
                    rotationData.page_number = currentPageNumber;
                } else if (currentImageType === 'dish' && currentDishNumber !== null) {
                    rotationData.image_type = 'dish';
                    rotationData.dish_number = currentDishNumber;
                }
                
                const response = await fetch(`/api/recipe/${currentRecipeId}/rotation`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(rotationData)
                });
                
                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.error || 'Failed to update rotation');
                }
                
                // Reload recipes to update the view tab (this will update thumbnails with new rotation)
                // Preserve current page and filters
                if (document.getElementById('view-tab').classList.contains('active')) {
                    // Save current state before reloading
                    const savedPage = currentPage;
                    const savedFilterText = recipeFilter ? recipeFilter.value : '';
                    await loadRecipes();
                    // Restore page if still valid
                    const totalPages = Math.max(1, Math.ceil(filteredRecipes.length / pageSize));
                    if (savedPage <= totalPages) {
                        currentPage = savedPage;
                        displayRecipes(filteredRecipes);
                    }
                }
            } catch (error) {
                console.error('Error updating rotation:', error);
                // Revert on error
                if (direction === 'clockwise') {
                    currentRotation = (currentRotation - 90 + 360) % 360;
                } else {
                    currentRotation = (currentRotation + 90) % 360;
                }
                updateRotationDisplay();
                updateImageOverlayTransform();
            }
        }

        rotateClockwise.addEventListener('click', function(e) {
            e.stopPropagation();
            rotateImage('clockwise');
        });

        rotateCounterClockwise.addEventListener('click', function(e) {
            e.stopPropagation();
            rotateImage('counterclockwise');
        });

        // Unneeded checkbox handler - set up at page load like rotation buttons
        const unneededCheckbox = document.getElementById('unneededCheckbox');
        if (unneededCheckbox) {
            // Use mousedown with capture phase to stop propagation BEFORE drag handler
            // Don't preventDefault - let checkbox toggle naturally
            unneededCheckbox.addEventListener('mousedown', function(e) {
                e.stopPropagation();
            }, true);
            
            // Handle click like rotation buttons do - use capture phase to ensure it fires
            unneededCheckbox.addEventListener('click', function(e) {
                e.stopPropagation();
                // Checkbox toggles naturally, then update status
                updateUnneededStatus(this.checked);
            }, true);
            
            // Also handle change event as backup
            unneededCheckbox.addEventListener('change', function(e) {
                e.stopPropagation();
                updateUnneededStatus(this.checked);
            });
            
            // Handle label clicks too - label clicks naturally trigger checkbox
            const unneededCheckboxLabel = document.querySelector('label[for="unneededCheckbox"]');
            if (unneededCheckboxLabel) {
                unneededCheckboxLabel.addEventListener('mousedown', function(e) {
                    e.stopPropagation();
                }, true);
                unneededCheckboxLabel.addEventListener('click', function(e) {
                    e.stopPropagation();
                    // Manually toggle checkbox if label is clicked (in case checkbox is hidden)
                    if (unneededCheckbox) {
                        unneededCheckbox.checked = !unneededCheckbox.checked;
                        updateUnneededStatus(unneededCheckbox.checked);
                    }
                });
            }
        }

        function updateUnneededCheckbox() {
            const checkbox = document.getElementById('unneededCheckbox');
            if (checkbox) {
                checkbox.checked = currentUnneeded;
                // Only show checkbox for recipe page images
                checkbox.disabled = currentImageType !== 'page' || currentPageNumber === null;
            }
        }

        function updateImageUnneededStyle() {
            if (previewImage) {
                if (currentUnneeded && currentImageType === 'page') {
                    previewImage.classList.add('image-unneeded');
                } else {
                    previewImage.classList.remove('image-unneeded');
                }
            }
        }

        async function updateUnneededStatus(unneeded) {
            if (!currentRecipeId || currentImageType !== 'page' || currentPageNumber === null) {
                return;
            }

            try {
                const response = await fetch(`/api/recipe/${currentRecipeId}/page/${currentPageNumber}/unneeded`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ unneeded: unneeded })
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.error || 'Failed to update unneeded status');
                }

                currentUnneeded = unneeded;
                updateImageUnneededStyle();
                
                // Update the current image group data
                if (currentImageGroup.length > 0 && currentImageIndex >= 0 && currentImageIndex < currentImageGroup.length) {
                    currentImageGroup[currentImageIndex].unneeded = unneeded;
                }
            } catch (error) {
                console.error('Error updating unneeded status:', error);
                // Revert checkbox
                updateUnneededCheckbox();
            }
        }

        function hideImagePreview() {
            imageOverlay.classList.remove('active');
            previewImage.src = '';
            previewImage.style.transform = '';
            previewImage.style.transformOrigin = 'center center';
            previewImage.classList.remove('image-unneeded');
            currentRecipeId = null;
            currentRotation = 0;
            currentImageType = null;
            currentPageNumber = null;
            currentDishNumber = null;
            currentImageIndex = 0;
            currentImageGroup = [];
            currentGroupType = null;
            imageOverlayZoomed = false;
            imageOverlayTransform = { x: 0, y: 0, scale: 1 };
            currentUnneeded = false;
            document.getElementById('imageNavLeft').style.display = 'none';
            document.getElementById('imageNavRight').style.display = 'none';
        }
        
        // Navigation arrow click handlers
        const imageNavLeft = document.getElementById('imageNavLeft');
        const imageNavRight = document.getElementById('imageNavRight');
        
        if (imageNavLeft) {
            imageNavLeft.addEventListener('click', function(e) {
                e.stopPropagation();
                navigateImage('prev');
            });
        }
        
        if (imageNavRight) {
            imageNavRight.addEventListener('click', function(e) {
                e.stopPropagation();
                navigateImage('next');
            });
        }
        
        // Keyboard navigation
        document.addEventListener('keydown', function(e) {
            if (imageOverlay.classList.contains('active')) {
                if (e.key === 'ArrowLeft') {
                    e.preventDefault();
                    navigateImage('prev');
                } else if (e.key === 'ArrowRight') {
                    e.preventDefault();
                    navigateImage('next');
                }
            }
        });

        // Close overlay when clicking close button, overlay background, or pressing Escape
        imageOverlayClose.addEventListener('click', hideImagePreview);
        imageOverlay.addEventListener('click', function(e) {
            if (e.target === imageOverlay) {
                hideImagePreview();
            }
        });

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && imageOverlay.classList.contains('active')) {
                hideImagePreview();
            }
        });

        // Click to zoom and drag to pan functionality for image overlay
        const imageOverlayContent = document.querySelector('.image-overlay-content');
        if (imageOverlayContent && previewImage) {
            let isDragging = false;
            let dragStartX = 0;
            let dragStartY = 0;
            let dragStartPosX = 0;
            let dragStartPosY = 0;
            let hasDragged = false;
            
            imageOverlayContent.addEventListener('mousedown', function(e) {
                // Don't handle if clicking on controls, navigation, close button, or unneeded checkbox
                // Check for checkbox first, before anything else
                if (e.target.id === 'unneededCheckbox' || 
                    e.target.closest('#unneededCheckbox') ||
                    e.target.closest('label[for="unneededCheckbox"]') ||
                    e.target.closest('.unneeded-checkbox-wrapper') ||
                    e.target.closest('.image-nav-arrow') || 
                    e.target.closest('.rotation-controls') ||
                    e.target.closest('.unneeded-checkbox') ||
                    e.target.closest('.unneeded-checkbox-label') ||
                    e.target.closest('.image-overlay-close') ||
                    e.target.closest('.image-overlay-title')) {
                    // Don't prevent default for these elements - let them handle their own events
                    return;
                }
                
                if (imageOverlayZoomed) {
                    // Start drag
                    isDragging = true;
                    hasDragged = false;
                    dragStartX = e.clientX;
                    dragStartY = e.clientY;
                    dragStartPosX = imageOverlayTransform.x;
                    dragStartPosY = imageOverlayTransform.y;
                    e.preventDefault();
                } else {
                    // Track for potential drag (even when not zoomed)
                    isDragging = true;
                    hasDragged = false;
                    dragStartX = e.clientX;
                    dragStartY = e.clientY;
                }
            });
            
            document.addEventListener('mousemove', function(e) {
                if (!isDragging) return;
                
                const deltaX = Math.abs(e.clientX - dragStartX);
                const deltaY = Math.abs(e.clientY - dragStartY);
                
                // If moved more than 5 pixels, consider it a drag
                if (deltaX > 5 || deltaY > 5) {
                    hasDragged = true;
                }
                
                if (imageOverlayZoomed && hasDragged) {
                    // Update pan position
                    imageOverlayTransform.x = dragStartPosX + (e.clientX - dragStartX);
                    imageOverlayTransform.y = dragStartPosY + (e.clientY - dragStartY);
                    updateImageOverlayTransform();
                }
            });
            
            imageOverlayContent.addEventListener('mouseup', function(e) {
                // First check if clicking on checkbox or controls - exit early before checking isDragging
                if (e.target.id === 'unneededCheckbox' || 
                    e.target.closest('#unneededCheckbox') ||
                    e.target.closest('label[for="unneededCheckbox"]') ||
                    e.target.closest('.unneeded-checkbox-wrapper') ||
                    e.target.closest('.image-nav-arrow') || 
                    e.target.closest('.rotation-controls') ||
                    e.target.closest('.unneeded-checkbox') ||
                    e.target.closest('.unneeded-checkbox-label') ||
                    e.target.closest('.image-overlay-close') ||
                    e.target.closest('.image-overlay-title')) {
                    // Reset dragging state and let the element handle its own click
                    isDragging = false;
                    hasDragged = false;
                    return;
                }
                
                if (!isDragging) return;
                
                // If it was a drag, don't toggle zoom
                if (hasDragged) {
                    isDragging = false;
                    hasDragged = false;
                    return;
                }
                
                // If it was just a click (no drag), toggle zoom
                if (!imageOverlayZoomed) {
                    toggleImageOverlayZoom();
                } else {
                    // If already zoomed and it's a click (not drag), zoom out
                    toggleImageOverlayZoom();
                }
                
                isDragging = false;
                hasDragged = false;
            });
        }

        // Event delegation for save buttons (works for dynamically added buttons)
        document.addEventListener('click', async function(e) {
            // Check if clicked element is the save button or inside it
            const saveBtn = e.target.closest('.save-recipe-btn');
            if (saveBtn) {
                e.preventDefault();
                e.stopPropagation();
                const recipeId = saveBtn.getAttribute('data-recipe-id');
                if (recipeId) {
                    console.log('Save button clicked via delegation for recipe', recipeId);
                    await saveRecipeChanges(parseInt(recipeId, 10));
                }
            }
        });
        
        // Edit Modal Functions
        async function openEditModal(recipeId) {
            const modal = document.getElementById('editModal');
            const form = document.getElementById('editRecipeForm');
            const image = document.getElementById('editModalImage');
            const imagePlaceholder = document.getElementById('editModalImagePlaceholder');
            const title = document.getElementById('editModalTitle');
            const container = document.getElementById('editModalImageContainer');
            
            if (!modal || !form) return;
            
            // Reset state
            editModalRecipeId = recipeId;
            editModalImages = [];
            editModalCurrentIndex = 0;
            editModalZoomed = false;
            editModalImageTransform = { x: 0, y: 0, scale: 1 };
            
            // Show modal
            modal.classList.add('active');
            
            // Reset form
            form.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; padding: 20px; color: #666;">Loading recipe data...</div>';
            image.style.display = 'none';
            imagePlaceholder.style.display = 'block';
            imagePlaceholder.textContent = 'Loading image...';
            if (container) {
                container.classList.remove('zoomed');
            }
            
            // Hide controls initially
            document.getElementById('editModalNavLeft').style.display = 'none';
            document.getElementById('editModalNavRight').style.display = 'none';
            document.getElementById('editModalImageControls').style.display = 'none';
            
            try {
                // Fetch recipe data
                const response = await fetch(`/api/recipe/${recipeId}`);
                if (!response.ok) {
                    throw new Error('Failed to load recipe');
                }
                
                const data = await response.json();
                
                // Set title
                title.textContent = `Edit: ${data.title || data.pdf_filename || 'Recipe'}`;
                
                // Build image list (pages + dish images)
                if (data.pages && data.pages.length > 0) {
                    data.pages.forEach(page => {
                        editModalImages.push({
                            type: 'page',
                            number: page.pdf_page_number,
                            rotation: page.rotation || 0,
                            unneeded: page.unneeded || false
                        });
                    });
                }
                
                if (data.dish_images && data.dish_images.length > 0) {
                    data.dish_images.forEach(dishImg => {
                        editModalImages.push({
                            type: 'dish',
                            number: dishImg.image_number,
                            rotation: dishImg.rotation || 0
                        });
                    });
                }
                
                // Load first image
                if (editModalImages.length > 0) {
                    loadEditModalImage(0);
                } else {
                    imagePlaceholder.textContent = 'No image available';
                }
                
                // Build form fields
                const stateOptions = ['not_started', 'partially_complete', 'complete', 'broken', 'duplicate'];
                const stateOptionLabels = {
                    'not_started': 'Not Started',
                    'partially_complete': 'In Progress',
                    'complete': 'Complete',
                    'broken': 'Broken',
                    'duplicate': 'Duplicate'
                };
                
                form.innerHTML = `
                    <div class="edit-form-label">State:</div>
                    <div>
                        <select class="edit-form-select" id="edit-state" data-field="state">
                            ${stateOptions.map(state => `<option value="${state}" ${data.state === state ? 'selected' : ''}>${stateOptionLabels[state]}</option>`).join('')}
                        </select>
                    </div>
                    
                    <div class="edit-form-label">Title:</div>
                    <div>
                        <input type="text" class="edit-form-input" id="edit-title" data-field="title" value="${escapeHtml(data.title || '')}" placeholder="Not set">
                    </div>
                    
                    <div class="edit-form-label">Description:</div>
                    <div>
                        <textarea class="edit-form-textarea" id="edit-description" data-field="description" placeholder="Not set">${escapeHtml(data.description || '')}</textarea>
                    </div>
                    
                    <div class="edit-form-label">Year:</div>
                    <div>
                        <input type="number" class="edit-form-input" id="edit-year" data-field="year" value="${data.year || ''}" placeholder="Not set">
                    </div>
                    
                    <div class="edit-form-label">Author:</div>
                    <div>
                        <input type="text" class="edit-form-input" id="edit-author" data-field="author" value="${escapeHtml(data.author || '')}" placeholder="Not set">
                    </div>
                    
                    <div class="edit-form-label">Ingredients:</div>
                    <div>
                        <textarea class="edit-form-textarea" id="edit-ingredients" data-field="ingredients" placeholder="Not set">${escapeHtml(data.ingredients || '')}</textarea>
                    </div>
                    
                    <div class="edit-form-label">Recipe:</div>
                    <div>
                        <textarea class="edit-form-textarea" id="edit-recipe" data-field="recipe" placeholder="Not set">${escapeHtml(data.recipe || '')}</textarea>
                    </div>
                    
                    <div class="edit-form-label">Cook Time:</div>
                    <div>
                        <input type="text" class="edit-form-input" id="edit-cook-time" data-field="cook_time" value="${escapeHtml(data.cook_time || '')}" placeholder="Not set">
                    </div>
                    
                    <div class="edit-form-label">Notes:</div>
                    <div>
                        <textarea class="edit-form-textarea" id="edit-notes" data-field="notes" placeholder="Not set">${escapeHtml(data.notes || '')}</textarea>
                    </div>
                    
                    <div class="edit-form-actions">
                        <button type="button" class="edit-form-save-btn" id="edit-save-btn" data-recipe-id="${recipeId}">💾 Save Changes</button>
                        <span class="edit-form-status" id="edit-status"></span>
                    </div>
                `;
                
                // Add save button handler
                const saveBtn = document.getElementById('edit-save-btn');
                if (saveBtn) {
                    saveBtn.addEventListener('click', function() {
                        saveEditRecipe(recipeId);
                    });
                }
                
            } catch (error) {
                console.error('Error loading recipe for edit:', error);
                form.innerHTML = `<div style="grid-column: 1 / -1; color: #c33; padding: 20px;">Error loading recipe: ${escapeHtml(error.message)}</div>`;
            }
        }

        function loadEditModalImage(index) {
            if (index < 0 || index >= editModalImages.length) return;
            
            editModalCurrentIndex = index;
            const imageData = editModalImages[index];
            const image = document.getElementById('editModalImage');
            const imagePlaceholder = document.getElementById('editModalImagePlaceholder');
            const navLeft = document.getElementById('editModalNavLeft');
            const navRight = document.getElementById('editModalNavRight');
            const controls = document.getElementById('editModalImageControls');
            
            // Build image URL
            let imageUrl;
            if (imageData.type === 'page') {
                imageUrl = `/api/recipe/${editModalRecipeId}/page/${imageData.number}/image`;
            } else {
                imageUrl = `/api/recipe/${editModalRecipeId}/dish/${imageData.number}/image`;
            }
            
            // Reset zoom and position
            editModalZoomed = false;
            editModalImageTransform = { x: 0, y: 0, scale: 1 };
            editModalCurrentRotation = imageData.rotation || 0;
            updateEditModalImageTransform();
            
            // Show/hide navigation
            if (editModalImages.length > 1) {
                navLeft.style.display = 'flex';
                navRight.style.display = 'flex';
            } else {
                navLeft.style.display = 'none';
                navRight.style.display = 'none';
            }
            
            // Show controls
            controls.style.display = 'flex';
            updateEditModalRotationDisplay();
            updateEditModalUnneededCheckbox();
            updateEditModalImageUnneededStyle();
            
            // Load image
            image.src = imageUrl;
            image.onload = function() {
                image.style.display = 'block';
                imagePlaceholder.style.display = 'none';
            };
            image.onerror = function() {
                imagePlaceholder.textContent = 'Image not available';
            };
        }

        function updateEditModalImageTransform() {
            const image = document.getElementById('editModalImage');
            const container = document.getElementById('editModalImageContainer');
            
            if (!image || !container) return;
            
            const rotation = editModalCurrentRotation || 0;
            const scale = editModalImageTransform.scale;
            const x = editModalImageTransform.x;
            const y = editModalImageTransform.y;
            
            image.style.transform = `translate(${x}px, ${y}px) scale(${scale}) rotate(${rotation}deg)`;
            
            if (editModalZoomed) {
                container.classList.add('zoomed');
            } else {
                container.classList.remove('zoomed');
            }
        }

        function updateEditModalRotationDisplay() {
            const display = document.getElementById('editModalRotationDisplay');
            if (display) {
                display.textContent = `${editModalCurrentRotation}°`;
            }
        }

        function updateEditModalUnneededCheckbox() {
            const checkbox = document.getElementById('editModalUnneededCheckbox');
            if (checkbox && editModalImages.length > 0 && editModalCurrentIndex >= 0) {
                const imageData = editModalImages[editModalCurrentIndex];
                checkbox.checked = imageData.unneeded || false;
                // Only enable checkbox for page images
                checkbox.disabled = imageData.type !== 'page';
            }
        }

        function updateEditModalImageUnneededStyle() {
            const image = document.getElementById('editModalImage');
            if (image && editModalImages.length > 0 && editModalCurrentIndex >= 0) {
                const imageData = editModalImages[editModalCurrentIndex];
                if (imageData.unneeded && imageData.type === 'page') {
                    image.classList.add('image-unneeded');
                } else {
                    image.classList.remove('image-unneeded');
                }
            }
        }

        async function updateEditModalUnneededStatus(unneeded) {
            if (!editModalRecipeId || editModalImages.length === 0) return;
            
            const imageData = editModalImages[editModalCurrentIndex];
            if (imageData.type !== 'page') return;

            try {
                const response = await fetch(`/api/recipe/${editModalRecipeId}/page/${imageData.number}/unneeded`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ unneeded: unneeded })
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.error || 'Failed to update unneeded status');
                }

                imageData.unneeded = unneeded;
                updateEditModalImageUnneededStyle();
            } catch (error) {
                console.error('Error updating unneeded status:', error);
                // Revert checkbox
                updateEditModalUnneededCheckbox();
            }
        }

        function toggleEditModalZoom() {
            editModalZoomed = !editModalZoomed;
            
            if (editModalZoomed) {
                editModalImageTransform.scale = 2;
            } else {
                editModalImageTransform.scale = 1;
                editModalImageTransform.x = 0;
                editModalImageTransform.y = 0;
            }
            
            updateEditModalImageTransform();
        }

        function closeEditModal() {
            const modal = document.getElementById('editModal');
            if (modal) {
                modal.classList.remove('active');
                // Reset state
                editModalZoomed = false;
                editModalImageTransform = { x: 0, y: 0, scale: 1 };
                const container = document.getElementById('editModalImageContainer');
                if (container) {
                    container.classList.remove('zoomed');
                }
            }
        }

        async function saveEditRecipe(recipeId) {
            const saveBtn = document.getElementById('edit-save-btn');
            const statusSpan = document.getElementById('edit-status');
            
            if (!saveBtn || !statusSpan) return;
            
            // Collect field values
            const fields = {};
            const inputs = document.querySelectorAll('#editRecipeForm [data-field]');
            
            inputs.forEach(input => {
                const fieldName = input.getAttribute('data-field');
                if (fieldName) {
                    if (input.tagName === 'TEXTAREA' || input.tagName === 'INPUT') {
                        fields[fieldName] = input.value || null;
                    } else if (input.tagName === 'SELECT') {
                        fields[fieldName] = input.value;
                    }
                }
            });
            
            // Convert year to number if provided
            if (fields.year !== null && fields.year !== undefined && fields.year !== '') {
                const yearNum = parseInt(fields.year, 10);
                if (!isNaN(yearNum)) {
                    fields.year = yearNum;
                } else {
                    fields.year = null;
                }
            } else {
                fields.year = null;
            }
            
            // Show saving status
            saveBtn.disabled = true;
            statusSpan.textContent = 'Saving...';
            statusSpan.style.color = '#666';
            
            try {
                const response = await fetch(`/api/recipe/${recipeId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(fields)
                });
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
                    throw new Error(errorData.error || 'Failed to save changes');
                }
                
                statusSpan.textContent = '✓ Saved successfully';
                statusSpan.style.color = '#28a745';
                
                // Reload recipes to update the view
                await loadRecipes();
                
                // Close modal after a short delay
                setTimeout(() => {
                    closeEditModal();
                }, 1000);
                
            } catch (error) {
                console.error('Save error:', error);
                statusSpan.textContent = '✗ Error: ' + error.message;
                statusSpan.style.color = '#c33';
            } finally {
                saveBtn.disabled = false;
            }
        }

        // Edit modal event handlers
        const editModal = document.getElementById('editModal');
        const editModalClose = document.getElementById('editModalClose');
        const editModalImage = document.getElementById('editModalImage');
        const editModalImageContainer = document.getElementById('editModalImageContainer');
        const editModalNavLeft = document.getElementById('editModalNavLeft');
        const editModalNavRight = document.getElementById('editModalNavRight');
        const editModalRotateCW = document.getElementById('editModalRotateCW');
        const editModalRotateCCW = document.getElementById('editModalRotateCCW');
        
        if (editModalClose) {
            editModalClose.addEventListener('click', closeEditModal);
        }
        
        if (editModal) {
            editModal.addEventListener('click', function(e) {
                if (e.target === editModal) {
                    closeEditModal();
                }
            });
        }
        
        // Drag to pan when zoomed and click to zoom
        if (editModalImageContainer) {
            let isDragging = false;
            let dragStartX = 0;
            let dragStartY = 0;
            let dragStartPosX = 0;
            let dragStartPosY = 0;
            let hasDragged = false;
            
            editModalImageContainer.addEventListener('mousedown', function(e) {
                // Don't handle if clicking on controls or navigation
                if (e.target.closest('.edit-modal-image-nav') || 
                    e.target.closest('.edit-modal-image-controls') ||
                    e.target.closest('.edit-modal-rotate-btn')) {
                    return;
                }
                
                if (editModalZoomed) {
                    // Start drag
                    isDragging = true;
                    hasDragged = false;
                    dragStartX = e.clientX;
                    dragStartY = e.clientY;
                    dragStartPosX = editModalImageTransform.x;
                    dragStartPosY = editModalImageTransform.y;
                    e.preventDefault();
                } else {
                    // Track for potential drag (even when not zoomed)
                    isDragging = true;
                    hasDragged = false;
                    dragStartX = e.clientX;
                    dragStartY = e.clientY;
                }
            });
            
            document.addEventListener('mousemove', function(e) {
                if (!isDragging) return;
                
                const deltaX = Math.abs(e.clientX - dragStartX);
                const deltaY = Math.abs(e.clientY - dragStartY);
                
                // If moved more than 5 pixels, consider it a drag
                if (deltaX > 5 || deltaY > 5) {
                    hasDragged = true;
                }
                
                if (editModalZoomed && hasDragged) {
                    // Update pan position
                    editModalImageTransform.x = dragStartPosX + (e.clientX - dragStartX);
                    editModalImageTransform.y = dragStartPosY + (e.clientY - dragStartY);
                    updateEditModalImageTransform();
                }
            });
            
            editModalImageContainer.addEventListener('mouseup', function(e) {
                if (!isDragging) return;
                
                // If it was a drag, don't toggle zoom
                if (hasDragged) {
                    isDragging = false;
                    hasDragged = false;
                    return;
                }
                
                // If it was just a click (no drag), toggle zoom
                if (!editModalZoomed) {
                    // Don't zoom if clicking on controls or navigation
                    if (e.target.closest('.edit-modal-image-nav') || 
                        e.target.closest('.edit-modal-image-controls') ||
                        e.target.closest('.edit-modal-rotate-btn')) {
                        isDragging = false;
                        hasDragged = false;
                        return;
                    }
                    toggleEditModalZoom();
                } else {
                    // If already zoomed and it's a click (not drag), zoom out
                    toggleEditModalZoom();
                }
                
                isDragging = false;
                hasDragged = false;
            });
        }
        
        // Navigation arrows
        if (editModalNavLeft) {
            editModalNavLeft.addEventListener('click', function(e) {
                e.stopPropagation();
                if (editModalCurrentIndex > 0) {
                    loadEditModalImage(editModalCurrentIndex - 1);
                } else {
                    loadEditModalImage(editModalImages.length - 1); // Wrap to last
                }
            });
        }
        
        if (editModalNavRight) {
            editModalNavRight.addEventListener('click', function(e) {
                e.stopPropagation();
                if (editModalCurrentIndex < editModalImages.length - 1) {
                    loadEditModalImage(editModalCurrentIndex + 1);
                } else {
                    loadEditModalImage(0); // Wrap to first
                }
            });
        }
        
        // Rotation buttons
        if (editModalRotateCW) {
            editModalRotateCW.addEventListener('click', async function(e) {
                e.stopPropagation();
                editModalCurrentRotation = (editModalCurrentRotation + 90) % 360;
                updateEditModalImageTransform();
                updateEditModalRotationDisplay();
                await saveEditModalRotation();
            });
        }
        
        if (editModalRotateCCW) {
            editModalRotateCCW.addEventListener('click', async function(e) {
                e.stopPropagation();
                editModalCurrentRotation = (editModalCurrentRotation - 90 + 360) % 360;
                updateEditModalImageTransform();
                updateEditModalRotationDisplay();
                await saveEditModalRotation();
            });
        }

        // Edit modal unneeded checkbox handler
        const editModalUnneededCheckbox = document.getElementById('editModalUnneededCheckbox');
        if (editModalUnneededCheckbox) {
            editModalUnneededCheckbox.addEventListener('change', function(e) {
                e.stopPropagation();
                updateEditModalUnneededStatus(this.checked);
            });
        }
        
        async function saveEditModalRotation() {
            if (!editModalRecipeId || editModalImages.length === 0) return;
            
            const imageData = editModalImages[editModalCurrentIndex];
            const rotationData = { rotation: editModalCurrentRotation };
            
            if (imageData.type === 'page') {
                rotationData.image_type = 'page';
                rotationData.page_number = imageData.number;
            } else {
                rotationData.image_type = 'dish';
                rotationData.dish_number = imageData.number;
            }
            
            try {
                const response = await fetch(`/api/recipe/${editModalRecipeId}/rotation`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(rotationData)
                });
                
                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.error || 'Failed to update rotation');
                }
                
                // Update the image data rotation
                imageData.rotation = editModalCurrentRotation;
            } catch (error) {
                console.error('Error updating rotation:', error);
                // Revert rotation on error
                editModalCurrentRotation = imageData.rotation || 0;
                updateEditModalImageTransform();
                updateEditModalRotationDisplay();
            }
        }
        
        // Keyboard navigation for edit modal
        document.addEventListener('keydown', function(e) {
            if (editModal && editModal.classList.contains('active')) {
                if (e.key === 'Escape') {
                    closeEditModal();
                } else if (e.key === 'ArrowLeft') {
                    e.preventDefault();
                    if (editModalNavLeft) editModalNavLeft.click();
                } else if (e.key === 'ArrowRight') {
                    e.preventDefault();
                    if (editModalNavRight) editModalNavRight.click();
                }
            }
        });

        // Load recipes on page load if View tab is active
        if (document.getElementById('view-tab').classList.contains('active')) {
            loadRecipes();
        }
