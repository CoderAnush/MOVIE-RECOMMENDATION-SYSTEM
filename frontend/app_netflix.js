/**
 * Netflix-Style Movie Recommender Frontend
 * Enhanced UI with smooth animations and professional interactions
 */

class NetflixMovieRecommender {
    constructor() {
        // API Configuration
        this.apiUrl = 'http://127.0.0.1:3000'; // Updated to match server port
        this.currentRecommendations = [];
        this.isLoading = false;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupSliders();
        this.checkSystemHealth();
        this.setupScrollEffects();
        this.setupCatalogSearch();
    }

    setupEventListeners() {
        // Form submission
        document.getElementById('preferences-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.getRecommendations();
        });

        // Sort functionality
        document.getElementById('sort-options').addEventListener('change', () => {
            this.sortRecommendations();
        });

        // Modal functionality
        const modal = document.getElementById('movie-modal');
        const closeBtn = document.querySelector('.close');
        
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });

        window.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                modal.style.display = 'none';
            }
            if (e.key === 'Enter' && e.ctrlKey) {
                this.getRecommendations();
            }
        });
    }

    setupSliders() {
        const sliders = document.querySelectorAll('.slider');
        sliders.forEach(slider => {
            const valueDisplay = document.getElementById(`${slider.id}-value`);
            
            // Update display on input
            slider.addEventListener('input', () => {
                let displayValue = slider.value;
                
                // Special formatting for percentage sliders
                if (slider.id.includes('weight') || slider.id === 'diversity') {
                    displayValue = slider.value + '%';
                }
                
                if (valueDisplay) {
                    valueDisplay.textContent = displayValue;
                }
                this.updateSliderColor(slider);
                
                // Clear previous errors when user changes preferences
                this.hideError();
                
                // Auto-adjust complementary AI weights
                if (slider.id === 'fuzzy-weight') {
                    const annSlider = document.getElementById('ann-weight');
                    const annDisplay = document.getElementById('ann-weight-value');
                    if (annSlider && annDisplay) {
                        const newAnnValue = 100 - parseInt(slider.value);
                        annSlider.value = newAnnValue;
                        annDisplay.textContent = newAnnValue + '%';
                        this.updateSliderColor(annSlider);
                    }
                } else if (slider.id === 'ann-weight') {
                    const fuzzySlider = document.getElementById('fuzzy-weight');
                    const fuzzyDisplay = document.getElementById('fuzzy-weight-value');
                    if (fuzzySlider && fuzzyDisplay) {
                        const newFuzzyValue = 100 - parseInt(slider.value);
                        fuzzySlider.value = newFuzzyValue;
                        fuzzyDisplay.textContent = newFuzzyValue + '%';
                        this.updateSliderColor(fuzzySlider);
                    }
                }
            });

            // Initialize display and color
            let displayValue = slider.value;
            if (slider.id.includes('weight') || slider.id === 'diversity') {
                displayValue = slider.value + '%';
            }
            if (valueDisplay) {
                valueDisplay.textContent = displayValue;
            }
            this.updateSliderColor(slider);
        });
    }

    updateSliderColor(slider) {
        const value = slider.value;
        const max = slider.max;
        const percentage = (value / max) * 100;
        
        // Create gradient based on value
        const hue = (percentage / 100) * 120; // 0 = red, 120 = green
        slider.style.background = `linear-gradient(90deg, 
            hsl(${hue}, 70%, 50%) 0%, 
            hsl(${hue}, 70%, 50%) ${percentage}%, 
            var(--netflix-light-gray) ${percentage}%, 
            var(--netflix-light-gray) 100%)`;
    }

    setupScrollEffects() {
        const header = document.getElementById('header');
        
        window.addEventListener('scroll', () => {
            if (window.scrollY > 100) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        });

        // Intersection Observer for animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-up');
                }
            });
        }, observerOptions);

        // Observe sections
        document.querySelectorAll('.preferences-section, #recommendations').forEach(section => {
            observer.observe(section);
        });
    }

    async checkSystemHealth() {
        try {
            const response = await fetch(`${this.apiUrl}/health`);
            const data = await response.json();
            
            const statusElement = document.getElementById('system-status');
            const messageElement = document.getElementById('status-message');
            
            if (data.status === 'healthy') {
                statusElement.className = 'alert alert-success';
                messageElement.textContent = `✅ System Ready - ${data.dataset_stats?.movies || 0} movies loaded`;
            } else {
                statusElement.className = 'alert alert-error';
                messageElement.textContent = '⚠️ System initializing... Please wait';
            }
            
            statusElement.style.display = 'block';
            
            // Auto-hide after 5 seconds if healthy
            if (data.status === 'healthy') {
                setTimeout(() => {
                    statusElement.style.display = 'none';
                }, 5000);
            }
            
        } catch (error) {
            console.error('Health check failed:', error);
            this.showError('Unable to connect to recommendation service');
        }
    }

    async loadMetrics() {
        try {
            // Load system metrics
            const metricsResponse = await fetch(`${this.apiUrl}/metrics`);
            const metrics = await metricsResponse.json();
            
            // Load system status
            const statusResponse = await fetch(`${this.apiUrl}/system/status`);
            const status = await statusResponse.json();
            
            this.displayMetrics(metrics, status);
            this.updateSystemStatus(status);
            
        } catch (error) {
            console.error('Failed to load metrics:', error);
            this.showError('Unable to load system metrics');
        }
    }

    displayMetrics(metrics, status) {
        // Dataset metrics
        const datasetStats = metrics.dataset_stats;
        document.getElementById('metric-dataset-size').textContent = 
            `${datasetStats.movies.toLocaleString()} Movies • ${(datasetStats.ratings/1000000).toFixed(1)}M Ratings • ${datasetStats.users.toLocaleString()} Users`;
        
        const topGenres = datasetStats.top_genres.slice(0, 5).join(', ');
        document.getElementById('metric-top-genres').textContent = `Top genres: ${topGenres}`;
        
        // ANN metrics
        const annMetrics = metrics.training_metrics.ann;
        document.getElementById('metric-ann-mae').textContent = `MAE: ${annMetrics.mae}`;
        document.getElementById('metric-ann-details').innerHTML = `
            RMSE: ${annMetrics.rmse} • R²: ${annMetrics.r2}<br>
            Epochs: ${annMetrics.epochs_trained} • ${annMetrics.architecture}
        `;
        
        // Fuzzy metrics
        const fuzzyMetrics = metrics.training_metrics.fuzzy;
        document.getElementById('metric-fuzzy-rules').textContent = `${fuzzyMetrics.rules} Rules`;
        document.getElementById('metric-fuzzy-details').innerHTML = `
            Preference Rules: ${fuzzyMetrics.rule_groups.preference_vs_genre}<br>
            Popularity Rules: ${fuzzyMetrics.rule_groups.popularity_genre_match}<br>
            History Rules: ${fuzzyMetrics.rule_groups.watch_history}
        `;
        
        // Performance metrics
        if (status.components && status.components.hybrid_system) {
            const perfTime = status.components.hybrid_system.last_prediction_time || '--';
            document.getElementById('metric-response-time').textContent = `${perfTime} ms`;
        }
        
        // Model architecture
        document.getElementById('metric-model-params').textContent = '3,905';
        document.getElementById('metric-architecture-details').innerHTML = `
            Dense Layers: 64→32→16→1<br>
            Dropout: 0.2, 0.15, 0.1<br>
            Input Features: 19 • Output: 1
        `;
        
        // Show metrics section
        document.getElementById('metrics').style.display = 'block';
    }

    updateSystemStatus(status) {
        // Update status indicators
        const apiStatus = document.getElementById('api-status');
        const fuzzyStatus = document.getElementById('fuzzy-status');
        const annStatus = document.getElementById('ann-status');
        
        // API Status
        apiStatus.textContent = status.status === 'healthy' ? '🟢' : '🔴';
        apiStatus.className = status.status === 'healthy' ? 'status-indicator online' : 'status-indicator';
        
        // Fuzzy Engine Status
        const fuzzyHealthy = status.components?.fuzzy_engine?.status === 'operational';
        fuzzyStatus.textContent = fuzzyHealthy ? '🟢' : '🔴';
        fuzzyStatus.className = fuzzyHealthy ? 'status-indicator online' : 'status-indicator';
        
        // ANN Model Status
        const annHealthy = status.components?.ann_model?.status === 'loaded';
        annStatus.textContent = annHealthy ? '🟢' : '🔴';
        annStatus.className = annHealthy ? 'status-indicator online' : 'status-indicator';
    }

    applyPreset(presetType) {
        // Remove active class from all preset buttons
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Add active class to clicked button
        event.target.classList.add('active');

        const presets = {
            action: { action: 9, thriller: 8, scifi: 7, drama: 4, comedy: 3, romance: 2, horror: 5, fantasy: 6, adventure: 8, crime: 6 },
            comedy: { comedy: 9, romance: 7, drama: 5, action: 4, scifi: 3, thriller: 2, horror: 1, fantasy: 4, animation: 7, adventure: 5 },
            drama: { drama: 9, romance: 7, thriller: 6, action: 4, comedy: 5, scifi: 3, horror: 2, fantasy: 4, crime: 6, mystery: 5 },
            scifi: { scifi: 9, action: 8, thriller: 7, fantasy: 6, drama: 4, comedy: 3, romance: 2, horror: 5, adventure: 7, animation: 4 },
            horror: { horror: 9, thriller: 8, action: 6, scifi: 5, drama: 3, comedy: 2, romance: 1, fantasy: 7, mystery: 7, crime: 5 },
            romance: { romance: 9, drama: 8, comedy: 7, fantasy: 5, action: 3, thriller: 2, scifi: 2, horror: 1, animation: 4, adventure: 4 },
            adventure: { adventure: 9, action: 8, fantasy: 7, scifi: 6, thriller: 5, drama: 4, comedy: 5, romance: 4, animation: 6, western: 5 },
            mystery: { mystery: 9, thriller: 8, crime: 8, drama: 7, action: 5, scifi: 4, horror: 6, comedy: 3, romance: 2, fantasy: 4 },
            fantasy: { fantasy: 9, adventure: 8, scifi: 6, action: 7, drama: 5, romance: 4, comedy: 4, thriller: 5, animation: 7, horror: 3 },
            animation: { animation: 9, comedy: 8, fantasy: 7, adventure: 6, family: 9, romance: 5, action: 4, drama: 6, scifi: 5, horror: 1 },
            classic: { drama: 8, romance: 7, thriller: 6, action: 5, comedy: 6, scifi: 3, horror: 4, fantasy: 3, crime: 6, western: 7 },
            modern: { action: 8, scifi: 8, thriller: 7, comedy: 7, drama: 6, fantasy: 7, horror: 5, romance: 5, adventure: 8, crime: 6 }
        };

        const preset = presets[presetType];
        if (preset) {
            Object.entries(preset).forEach(([genre, value]) => {
                const slider = document.getElementById(genre);
                const valueDisplay = document.getElementById(`${genre}-value`);
                if (slider && valueDisplay) {
                    slider.value = value;
                    valueDisplay.textContent = value;
                    this.updateSliderColor(slider);
                }
            });

            // Add smooth animation effect
            document.querySelectorAll('.preference-item').forEach((item, index) => {
                setTimeout(() => {
                    item.style.transform = 'scale(1.05)';
                    setTimeout(() => {
                        item.style.transform = 'scale(1)';
                    }, 200);
                }, index * 50);
            });
        }
    }

    applyMood(moodType) {
        // Remove active styling from all mood buttons
        document.querySelectorAll('.mood-btn').forEach(btn => {
            btn.classList.remove('active');
            btn.style.background = 'linear-gradient(135deg, var(--netflix-dark-gray), var(--netflix-gray))';
        });

        // Add active styling to clicked button
        event.target.classList.add('active');
        event.target.style.background = 'linear-gradient(135deg, var(--netflix-red), var(--netflix-dark-red))';

        const moods = {
            chill: { 
                genres: { comedy: 8, romance: 7, drama: 6, animation: 7, fantasy: 5, action: 3, thriller: 2, horror: 1 },
                settings: { 'min-rating': 6.5, 'popularity-weight': 'medium', 'diversity': 20 }
            },
            intense: { 
                genres: { action: 9, thriller: 9, horror: 8, crime: 8, scifi: 7, drama: 5, adventure: 8, mystery: 7 },
                settings: { 'min-rating': 7.0, 'popularity-weight': 'high', 'diversity': 10 }
            },
            emotional: { 
                genres: { drama: 9, romance: 8, family: 7, animation: 6, fantasy: 5, comedy: 4, action: 2, horror: 1 },
                settings: { 'min-rating': 7.5, 'popularity-weight': 'medium', 'diversity': 15 }
            },
            family: { 
                genres: { animation: 9, family: 9, comedy: 8, adventure: 7, fantasy: 7, romance: 4, drama: 5, action: 3 },
                settings: { 'min-rating': 6.0, 'family-friendly': true, 'no-violence': true, 'diversity': 25 }
            },
            date: { 
                genres: { romance: 9, comedy: 8, drama: 7, fantasy: 6, thriller: 4, action: 3, scifi: 3, horror: 1 },
                settings: { 'min-rating': 7.0, 'popularity-weight': 'medium', 'diversity': 20 }
            },
            solo: { 
                genres: { thriller: 8, mystery: 8, scifi: 7, drama: 7, crime: 6, horror: 6, action: 5, fantasy: 6 },
                settings: { 'min-rating': 7.0, 'popularity-weight': 'low', 'diversity': 40 }
            },
            brainy: { 
                genres: { scifi: 8, drama: 8, mystery: 7, thriller: 6, crime: 6, documentary: 9, biography: 8, history: 7 },
                settings: { 'min-rating': 7.5, 'award-winners': true, 'diversity': 30 }
            },
            escapist: { 
                genres: { fantasy: 9, scifi: 8, adventure: 8, animation: 7, action: 7, comedy: 6, romance: 5, horror: 3 },
                settings: { 'min-rating': 6.5, 'popularity-weight': 'high', 'diversity': 15 }
            }
        };

        const mood = moods[moodType];
        if (mood) {
            // Apply genre preferences
            Object.entries(mood.genres).forEach(([genre, value]) => {
                const slider = document.getElementById(genre);
                const valueDisplay = document.getElementById(`${genre}-value`);
                if (slider && valueDisplay) {
                    slider.value = value;
                    valueDisplay.textContent = value;
                    this.updateSliderColor(slider);
                }
            });

            // Apply additional settings
            Object.entries(mood.settings).forEach(([setting, value]) => {
                const element = document.getElementById(setting);
                if (element) {
                    if (element.type === 'checkbox') {
                        element.checked = value === true;
                    } else if (element.type === 'number' || element.type === 'range') {
                        element.value = value;
                        const valueDisplay = document.getElementById(`${setting}-value`);
                        if (valueDisplay) {
                            valueDisplay.textContent = typeof value === 'number' ? 
                                (setting.includes('weight') ? `${value}%` : value) : value;
                        }
                    } else if (element.tagName === 'SELECT') {
                        element.value = value;
                    }
                }
            });

            // Add smooth animation effect for mood selection
            document.querySelectorAll('.preference-item').forEach((item, index) => {
                setTimeout(() => {
                    item.style.transform = 'scale(1.02)';
                    setTimeout(() => {
                        item.style.transform = 'scale(1)';
                    }, 150);
                }, index * 25);
            });
        }
    }

    async getRecommendations() {
        if (this.isLoading) {
            console.log('Request already in progress, ignoring duplicate request');
            return;
        }

        this.isLoading = true;
        this.showLoading(true);
        this.hideError();
        
        // Disable the get recommendations button to prevent spam clicks
        const getRecsButton = document.querySelector('button[onclick="movieApp.getRecommendations()"]');
        if (getRecsButton) {
            getRecsButton.disabled = true;
            getRecsButton.textContent = 'Getting Recommendations...';
        }

        try {
            const requestData = this.prepareEnhancedRecommendationRequest();
            
            // Debug logging
            console.log('Sending recommendation request:', requestData);
            
            // Validate request data before sending
            if (!requestData.user_preferences || Object.keys(requestData.user_preferences).length === 0) {
                throw new Error('No user preferences specified');
            }
            
            // Ensure required fields are present
            const requiredFields = ['action', 'comedy', 'romance', 'thriller', 'drama', 'horror'];
            for (const field of requiredFields) {
                if (!(field in requestData.user_preferences)) {
                    requestData.user_preferences[field] = 5.0; // Default value
                }
            }
            
            const response = await fetch(`${this.apiUrl}/recommend/enhanced`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Server response error:', errorText);
                
                let errorDetail = response.statusText;
                try {
                    const errorData = JSON.parse(errorText);
                    if (errorData.detail) {
                        errorDetail = errorData.detail;
                    }
                } catch (e) {
                    // Use response text if not JSON
                    if (errorText) {
                        errorDetail = errorText;
                    }
                }
                
                throw new Error(`HTTP ${response.status}: ${errorDetail}`);
            }

            const data = await response.json();
            console.log('Received recommendation response:', data);
            
            if (data.detail) {
                throw new Error(data.detail);
            }

            if (!data.recommendations || !Array.isArray(data.recommendations)) {
                throw new Error('Invalid response format: no recommendations array');
            }

            this.currentRecommendations = data.recommendations;
            this.displayRecommendations(data);
            
            // Smooth scroll to results
            setTimeout(() => {
                document.getElementById('recommendations').scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }, 500);

        } catch (error) {
            console.error('Error getting recommendations:', error);
            
            let errorMessage = 'Failed to get recommendations';
            
            if (error.message.includes('422')) {
                errorMessage = 'Invalid preferences. Please check your settings and try again.';
            } else if (error.message.includes('500')) {
                errorMessage = 'Server error. Please try again in a moment.';
            } else if (error.message.includes('Failed to fetch')) {
                errorMessage = 'Cannot connect to server. Please make sure the server is running.';
            } else {
                errorMessage = `Failed to get recommendations: ${error.message}`;
            }
            
            this.showError(errorMessage);
            
            // Clear previous recommendations on error
            this.currentRecommendations = [];
            const moviesGrid = document.getElementById('movies-grid');
            if (moviesGrid) {
                moviesGrid.innerHTML = '<div style="text-align: center; color: var(--netflix-text-gray); padding: 2rem;">Please adjust your preferences and try again.</div>';
            }
        } finally {
            this.isLoading = false;
            this.showLoading(false);
            
            // Re-enable the get recommendations button
            const getRecsButton = document.querySelector('button[onclick="movieApp.getRecommendations()"]');
            if (getRecsButton) {
                getRecsButton.disabled = false;
                getRecsButton.textContent = '🎯 Get Recommendations';
            }
        }
    }

    prepareRecommendationRequest() {
        // Collect user preferences
        const userPreferences = {};
        const sliders = document.querySelectorAll('.slider');
        
        // Map frontend field names to API field names
        const fieldMapping = {
            'scifi': 'sci_fi',
            'fantasy': 'sci_fi'  // Map fantasy to sci_fi since API doesn't have fantasy
        };
        
        sliders.forEach(slider => {
            const fieldName = fieldMapping[slider.id] || slider.id.replace('-', '_');
            // Only include fields that are expected by the API
            if (['action', 'comedy', 'romance', 'thriller', 'sci_fi', 'drama', 'horror'].includes(fieldName)) {
                userPreferences[fieldName] = parseFloat(slider.value);
            }
        });
        
        // Ensure all required fields are present with default values
        const requiredFields = ['action', 'comedy', 'romance', 'thriller', 'sci_fi', 'drama', 'horror'];
        requiredFields.forEach(field => {
            if (userPreferences[field] === undefined) {
                userPreferences[field] = 5.0;  // Default value
            }
        });
        
        // Get number of recommendations requested
        const numRecommendations = parseInt(document.getElementById('num-recommendations').value) || 10;
        
        // Sample movies for demonstration - in a real app, this would come from a catalog
        const sampleMovies = [
            {
                title: "The Matrix",
                genres: ["Action", "Sci-Fi"],
                popularity: 95,
                year: 1999
            },
            {
                title: "The Shawshank Redemption", 
                genres: ["Drama"],
                popularity: 98,
                year: 1994
            },
            {
                title: "Inception",
                genres: ["Action", "Sci-Fi", "Thriller"],
                popularity: 92,
                year: 2010
            },
            {
                title: "Pulp Fiction",
                genres: ["Crime", "Drama"],
                popularity: 89,
                year: 1994
            },
            {
                title: "The Dark Knight",
                genres: ["Action", "Crime", "Drama"],
                popularity: 96,
                year: 2008
            },
            {
                title: "Forrest Gump",
                genres: ["Drama", "Romance"],
                popularity: 87,
                year: 1994
            },
            {
                title: "The Lord of the Rings: The Return of the King",
                genres: ["Adventure", "Drama", "Fantasy"],
                popularity: 94,
                year: 2003
            },
            {
                title: "The Godfather",
                genres: ["Crime", "Drama"],
                popularity: 97,
                year: 1972
            },
            {
                title: "Goodfellas",
                genres: ["Crime", "Drama"],
                popularity: 86,
                year: 1990
            },
            {
                title: "Interstellar",
                genres: ["Adventure", "Drama", "Sci-Fi"],
                popularity: 88,
                year: 2014
            }
        ].slice(0, numRecommendations);
        
        // Sample watch history
        const watchHistory = {
            liked_ratio: 0.75,
            disliked_ratio: 0.15,
            watch_count: Math.floor(Math.random() * 50) + 10
        };
        
        return {
            user_preferences: userPreferences,
            movies: sampleMovies,
            watch_history: watchHistory,
            strategy: "adaptive"
        };
    }

    prepareEnhancedRecommendationRequest() {
        // Collect user preferences
        const userPreferences = {};
        const sliders = document.querySelectorAll('.slider');
        
        // Map frontend field names to API field names and collect all preferences
        const fieldMapping = {
            'scifi': 'sci_fi',
            'sci-fi': 'sci_fi'
        };
        
        sliders.forEach(slider => {
            if (!slider.id) return; // Skip sliders without ID
            
            const fieldName = fieldMapping[slider.id] || slider.id.replace('-', '_');
            const value = parseFloat(slider.value);
            
            // Validate the value is within expected range
            if (!isNaN(value) && value >= 0 && value <= 10) {
                userPreferences[fieldName] = value;
            }
        });
        
        // Ensure core required fields are present with default values
        const coreFields = ['action', 'comedy', 'romance', 'thriller', 'sci_fi', 'drama', 'horror'];
        coreFields.forEach(field => {
            if (userPreferences[field] === undefined || isNaN(userPreferences[field])) {
                userPreferences[field] = 5.0;  // Default value
            }
            // Ensure values are within valid range
            userPreferences[field] = Math.max(0, Math.min(10, userPreferences[field]));
        });
        
        console.log('Prepared user preferences:', userPreferences);
        
        // Collect advanced preferences
        const advancedPrefs = {};
        
        // Year filters
        const minYear = document.getElementById('min-year')?.value;
        const maxYear = document.getElementById('max-year')?.value;
        if (minYear) advancedPrefs.min_year = parseInt(minYear);
        if (maxYear) advancedPrefs.max_year = parseInt(maxYear);
        
        // Rating filter
        const minRating = document.getElementById('min-rating')?.value;
        if (minRating) advancedPrefs.min_rating = parseFloat(minRating);
        
        // Popularity weight
        const popularityWeight = document.getElementById('popularity-weight')?.value;
        if (popularityWeight) advancedPrefs.popularity_weight = popularityWeight;
        
        // Content filters
        const familyFriendly = document.getElementById('family-friendly')?.checked;
        const noViolence = document.getElementById('no-violence')?.checked;
        const subtitlesOk = document.getElementById('subtitles-ok')?.checked;
        const awardWinners = document.getElementById('award-winners')?.checked;
        
        if (familyFriendly) advancedPrefs.family_friendly = true;
        if (noViolence) advancedPrefs.no_violence = true;
        if (subtitlesOk) advancedPrefs.subtitles_ok = true;
        if (awardWinners) advancedPrefs.award_winners = true;
        
        // AI engine weights
        const fuzzyWeight = document.getElementById('fuzzy-weight')?.value;
        const annWeight = document.getElementById('ann-weight')?.value;
        const diversity = document.getElementById('diversity')?.value;
        
        if (fuzzyWeight) advancedPrefs.fuzzy_weight = parseInt(fuzzyWeight) / 100;
        if (annWeight) advancedPrefs.ann_weight = parseInt(annWeight) / 100;
        if (diversity) advancedPrefs.diversity = parseInt(diversity) / 100;
        
        // Watched movies
        const watchedMoviesInput = document.getElementById('watched-movies')?.value;
        const watchedMovies = watchedMoviesInput 
            ? watchedMoviesInput.split(',').map(movie => movie.trim()).filter(movie => movie)
            : [];
        
        // Get number of recommendations requested
        const numRecommendations = parseInt(document.getElementById('num-recommendations').value) || 10;
        
        return {
            user_preferences: userPreferences,
            num_recommendations: numRecommendations,
            watched_movies: watchedMovies,
            advanced_preferences: advancedPrefs
        };
    }

    collectFormData() {
        const preferences = {};
        const sliders = document.querySelectorAll('.slider');
        
        sliders.forEach(slider => {
            preferences[slider.id] = parseInt(slider.value);
        });

        const watchedMoviesInput = document.getElementById('watched-movies').value;
        const watchedMovies = watchedMoviesInput 
            ? watchedMoviesInput.split(',').map(movie => movie.trim()).filter(movie => movie)
            : [];

        const numRecommendations = parseInt(document.getElementById('num-recommendations').value) || 10;

        return {
            user_preferences: preferences,
            watched_movies: watchedMovies,
            top_k: numRecommendations  // No limit - unlimited recommendations!
        };
    }

    displayRecommendations(data) {
        const recommendationsSection = document.getElementById('recommendations');
        const moviesGrid = document.getElementById('movies-grid');
        
        recommendationsSection.style.display = 'block';
        moviesGrid.innerHTML = '';

        if (!this.currentRecommendations.length) {
            moviesGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 3rem;">
                    <h3 style="color: var(--netflix-text-gray);">No recommendations found</h3>
                    <p style="color: var(--netflix-text-gray);">Try adjusting your preferences</p>
                </div>
            `;
            return;
        }

        this.currentRecommendations.forEach((movie, index) => {
            const movieCard = this.createMovieCard(movie, index);
            moviesGrid.appendChild(movieCard);
        });

        // Add staggered animation
        const cards = moviesGrid.querySelectorAll('.movie-card');
        cards.forEach((card, index) => {
            setTimeout(() => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(30px)';
                card.style.transition = 'all 0.6s ease';
                
                setTimeout(() => {
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, 50);
            }, index * 100);
        });
    }

    createMovieCard(movie, index) {
        const card = document.createElement('div');
        card.className = 'movie-card';
        
        // Extract movie data (Enhanced format with real movies)
        const title = movie.title || movie.movie_title || 'Unknown Movie';
        const year = movie.year || '';
        const genres = Array.isArray(movie.genres) ? movie.genres.join(', ') : (movie.genres || 'Unknown');
        const posterUrl = movie.poster_url || movie.poster || 'https://via.placeholder.com/300x450?text=No+Poster';
        const description = movie.description || '';
        const director = movie.director || 'Unknown';
        const cast = Array.isArray(movie.cast) ? movie.cast.slice(0, 3).join(', ') : (movie.cast || 'Unknown');
        const runtime = movie.runtime ? `${movie.runtime} min` : 'Unknown';
        
        // Scores (support both old and new format)
        const predictedRating = movie.predicted_rating || movie.hybrid_score || movie.score || 0;
        const confidence = movie.confidence || (movie.agreement || 0);
        const imdbRating = movie.rating || movie.avg_rating || 0;
        
        // Optimize poster URL - use smaller size if from TMDB
        let optimizedPosterUrl = posterUrl;
        if (posterUrl.includes('tmdb.org')) {
            // Change w500 to w300 for faster loading
            optimizedPosterUrl = posterUrl.replace('/w500/', '/w300/');
        }
        
        // Generate star rating based on predicted score
        const stars = this.generateStarRating(predictedRating);
        
        // Score colors
        const scoreColor = this.getScoreColor(predictedRating);
        const confidenceColor = confidence > 0.8 ? '#46d369' : confidence > 0.6 ? '#f5c842' : '#E50914';
        
        card.innerHTML = `
            <div class="movie-poster-container">
                <div class="movie-rank">#${index + 1}</div>
                <img class="movie-poster-img" src="${optimizedPosterUrl}" alt="${title}" loading="lazy" decoding="async"
                     onerror="this.onerror=null; this.src='https://via.placeholder.com/300x450/141414/E50914?text=${encodeURIComponent(title.substring(0, 20))}';"
                     onload="this.style.opacity='1'; this.parentElement.querySelector('.poster-loading')?.remove();"
                     style="opacity: 0; transition: opacity 0.3s ease;">
                <div class="poster-loading" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #E50914; font-size: 1.2rem;">
                    🎬 Loading...
                </div>
                <div class="poster-overlay">
                    <div class="predicted-score" style="background: ${scoreColor};">
                        <span class="score-number">${predictedRating.toFixed(1)}</span>
                        <span class="score-label">Predicted</span>
                    </div>
                    <div class="confidence-badge" style="background: ${confidenceColor};">
                        <span class="confidence-icon">${confidence > 0.8 ? '🎯' : confidence > 0.6 ? '👍' : '🤔'}</span>
                        <span class="confidence-text">${(confidence * 100).toFixed(0)}% Match</span>
                    </div>
                </div>
            </div>
            <div class="movie-info">
                <h3 class="movie-title">${title}</h3>
                <div class="movie-year-runtime">${year} • ${runtime}</div>
                <div class="movie-genres">${genres}</div>
                
                <div class="movie-details">
                    <div class="detail-row">
                        <span class="detail-label">Director:</span>
                        <span class="detail-value">${director}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Cast:</span>
                        <span class="detail-value">${cast}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">IMDb:</span>
                        <span class="detail-value">${imdbRating}/10</span>
                    </div>
                </div>
                
                <div class="rating-stars">${stars}</div>
                
                ${description ? `
                    <div class="movie-description">
                        <p>${description.length > 120 ? description.substring(0, 120) + '...' : description}</p>
                    </div>
                ` : ''}
                
                ${movie.explanation ? `
                    <div class="recommendation-reason">
                        <div class="reason-header">
                            <strong>🎯 Why We Recommend This</strong>
                        </div>
                        <div class="reason-content">
                            <p>${movie.explanation}</p>
                        </div>
                    </div>
                ` : ''}
                
                ${(movie.fuzzy_score || movie.ann_score || movie.hybrid_score) ? `
                    <div class="model-scores">
                        <div class="scores-header">
                            <strong>🤖 AI Model Scores</strong>
                        </div>
                        <div class="scores-grid">
                            ${movie.hybrid_score ? `
                                <div class="score-item overall">
                                    <span class="score-value">${movie.hybrid_score.toFixed(1)}</span>
                                    <span class="score-label">Overall Score</span>
                                </div>
                            ` : ''}
                            ${movie.fuzzy_score ? `
                                <div class="score-item fuzzy">
                                    <span class="score-value">${movie.fuzzy_score.toFixed(1)}</span>
                                    <span class="score-label">Fuzzy Logic</span>
                                </div>
                            ` : ''}
                            ${movie.ann_score ? `
                                <div class="score-item neural">
                                    <span class="score-value">${movie.ann_score.toFixed(1)}</span>
                                    <span class="score-label">Neural Network</span>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;

        card.addEventListener('click', () => {
            this.showMovieDetails(movie);
        });

        return card;
    }

    generateStarRating(rating) {
        const fullStars = Math.floor(rating / 2); // Convert 10-point to 5-point scale
        const halfStar = (rating % 2) >= 1;
        const emptyStars = 5 - fullStars - (halfStar ? 1 : 0);
        
        return '★'.repeat(fullStars) + (halfStar ? '☆' : '') + '☆'.repeat(emptyStars);
    }

    getScoreColor(score) {
        if (score >= 8) return 'var(--success-green)';
        if (score >= 6) return 'var(--warning-yellow)';
        if (score >= 4) return 'var(--info-blue)';
        return 'var(--netflix-red)';
    }

    showMovieDetails(movie) {
        const modal = document.getElementById('movie-modal');
        const modalContent = document.getElementById('modal-content');
        
        const genres = Array.isArray(movie.genres) ? movie.genres.join(', ') : movie.genres || 'Unknown';
        const year = movie.year ? `(${movie.year})` : '';
        const rating = movie.avg_rating ? parseFloat(movie.avg_rating).toFixed(1) : 'N/A';
        const stars = this.generateStarRating(movie.avg_rating || 0);
        
        modalContent.innerHTML = `
            <div style="text-align: center; margin-bottom: 2rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🎬</div>
                <h2 style="color: var(--netflix-white); margin-bottom: 0.5rem;">${movie.title} ${year}</h2>
                <div style="color: var(--netflix-text-gray); margin-bottom: 1rem;">${genres}</div>
                <div style="color: var(--warning-yellow); font-size: 1.2rem;">${stars} ${rating}/10</div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
                <div style="background: var(--netflix-gray); padding: 1rem; border-radius: 8px; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 600; color: var(--netflix-red);">${(movie.score || movie.hybrid_score || movie.predicted_rating || 0).toFixed(1)}</div>
                    <div style="color: var(--netflix-text-gray);">Overall Score</div>
                </div>
                <div style="background: var(--netflix-gray); padding: 1rem; border-radius: 8px; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 600; color: var(--success-green);">${(movie.fuzzy_score || 0).toFixed(2)}</div>
                    <div style="color: var(--netflix-text-gray);">Fuzzy Logic</div>
                </div>
                <div style="background: var(--netflix-gray); padding: 1rem; border-radius: 8px; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 600; color: var(--info-blue);">${(movie.ann_score || 0).toFixed(2)}</div>
                    <div style="color: var(--netflix-text-gray);">Neural Network</div>
                </div>
            </div>
            
            <div style="background: var(--netflix-gray); padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem;">
                <h4 style="color: var(--netflix-white); margin-bottom: 1rem;">🎯 Why We Recommend This</h4>
                <p style="color: var(--netflix-text-gray); line-height: 1.6;">${movie.explanation || 'This movie matches your preferences based on our AI analysis.'}</p>
            </div>
            
            ${movie.rating_count ? `
                <div style="text-align: center; color: var(--netflix-text-gray);">
                    Based on ${movie.rating_count} user ratings
                </div>
            ` : ''}
        `;
        
        modal.style.display = 'block';
        
        // Add entrance animation
        modalContent.style.transform = 'scale(0.8)';
        modalContent.style.opacity = '0';
        setTimeout(() => {
            modalContent.style.transition = 'all 0.3s ease';
            modalContent.style.transform = 'scale(1)';
            modalContent.style.opacity = '1';
        }, 10);
    }

    sortRecommendations() {
        const sortBy = document.getElementById('sort-options').value;
        
        if (!this.currentRecommendations.length) return;
        
        const sorted = [...this.currentRecommendations].sort((a, b) => {
            switch (sortBy) {
                case 'fuzzy_score':
                    return (b.fuzzy_score || 0) - (a.fuzzy_score || 0);
                case 'ann_score':
                    return (b.ann_score || 0) - (a.ann_score || 0);
                case 'title':
                    return (a.title || '').localeCompare(b.title || '');
                case 'year':
                    return (b.year || 0) - (a.year || 0);
                default: // score
                    return (b.score || 0) - (a.score || 0);
            }
        });
        
        this.currentRecommendations = sorted;
        this.displayRecommendations({ recommendations: sorted });
    }

    exportResults() {
        if (!this.currentRecommendations.length) {
            this.showError('No recommendations to export');
            return;
        }

        const csvContent = this.generateCSV(this.currentRecommendations);
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `movie_recommendations_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        // Show success message
        const statusElement = document.getElementById('system-status');
        const messageElement = document.getElementById('status-message');
        statusElement.className = 'alert alert-success';
        messageElement.textContent = '💾 Recommendations exported successfully!';
        statusElement.style.display = 'block';
        
        setTimeout(() => {
            statusElement.style.display = 'none';
        }, 3000);
    }

    generateCSV(recommendations) {
        const headers = ['Title', 'Year', 'Genres', 'Overall Score', 'Fuzzy Score', 'Neural Score', 'Rating', 'Explanation'];
        const rows = recommendations.map(movie => [
            `"${movie.title || ''}"`,
            movie.year || '',
            `"${Array.isArray(movie.genres) ? movie.genres.join(', ') : movie.genres || ''}"`,
            (movie.score || 0).toFixed(2),
            (movie.fuzzy_score || 0).toFixed(2),
            (movie.ann_score || 0).toFixed(2),
            (movie.avg_rating || 0).toFixed(1),
            `"${movie.explanation || ''}"`
        ]);
        
        return [headers, ...rows].map(row => row.join(',')).join('\n');
    }

    resetForm() {
        // Reset all sliders to 5
        document.querySelectorAll('.slider').forEach(slider => {
            slider.value = 5;
            const valueDisplay = document.getElementById(`${slider.id}-value`);
            valueDisplay.textContent = '5';
            this.updateSliderColor(slider);
        });

        // Clear text inputs
        document.getElementById('watched-movies').value = '';
        document.getElementById('num-recommendations').value = '10';

        // Remove active preset
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Hide results
        document.getElementById('recommendations').style.display = 'none';
        this.hideError();
    }

    showLoading(show) {
        const loading = document.getElementById('loading');
        const button = document.getElementById('get-recommendations');
        
        if (show) {
            loading.style.display = 'flex';
            button.textContent = '🔄 Finding Movies...';
            button.disabled = true;
        } else {
            loading.style.display = 'none';
            button.textContent = '🎯 Get My Recommendations';
            button.disabled = false;
        }
    }

    showError(message) {
        const errorElement = document.getElementById('error-message');
        const errorText = document.getElementById('error-text');
        
        errorText.textContent = message;
        errorElement.style.display = 'block';
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            this.hideError();
        }, 10000);
    }

    hideError() {
        document.getElementById('error-message').style.display = 'none';
    }

    // Movie Catalog Functions
    async showCatalog() {
        // Hide other sections
        document.getElementById('recommendations').style.display = 'none';
        document.getElementById('preferences').style.display = 'none';
        
        // Show catalog section
        const catalogSection = document.getElementById('catalog');
        catalogSection.style.display = 'block';
        
        // Load genres for filter
        await this.loadGenresForCatalog();
        
        // Load first page of movies
        await this.loadCatalog(1);
        
        // Scroll to catalog
        catalogSection.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }

    async loadGenresForCatalog() {
        try {
            const response = await fetch(`${this.apiUrl}/genres`);
            const data = await response.json();
            
            const genreSelect = document.getElementById('catalog-genre');
            genreSelect.innerHTML = '<option value="">All Genres</option>';
            
            data.genres.forEach(genre => {
                const option = document.createElement('option');
                option.value = genre;
                option.textContent = genre;
                genreSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading genres:', error);
        }
    }

    async loadCatalog(page = 1) {
        try {
            this.showLoading(true);
            
            // Get filter values
            const sortBy = document.getElementById('catalog-sort').value;
            const genre = document.getElementById('catalog-genre').value;
            const yearMin = document.getElementById('catalog-year-min').value;
            const yearMax = document.getElementById('catalog-year-max').value;
            const ratingMin = document.getElementById('catalog-rating-min').value;
            
            // Build query parameters
            const params = new URLSearchParams({
                page: page,
                per_page: 50,
                sort_by: sortBy
            });
            
            if (genre) params.append('genre', genre);
            if (yearMin) params.append('year_min', yearMin);
            if (yearMax) params.append('year_max', yearMax);
            if (ratingMin) params.append('rating_min', ratingMin);
            
            const response = await fetch(`${this.apiUrl}/movies/browse?${params}`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.displayCatalogMovies(data.movies);
            this.displayCatalogPagination(data.pagination);
            this.displayCatalogStats(data.pagination);
            
        } catch (error) {
            console.error('Error loading catalog:', error);
            this.showError(`Failed to load catalog: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }

    displayCatalogMovies(movies) {
        const catalogGrid = document.getElementById('catalog-grid');
        catalogGrid.innerHTML = '';
        
        if (!movies.length) {
            catalogGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 3rem;">
                    <h3 style="color: var(--netflix-text-gray);">No movies found</h3>
                    <p style="color: var(--netflix-text-gray);">Try adjusting your filters</p>
                </div>
            `;
            return;
        }
        
        movies.forEach((movie, index) => {
            const movieCard = this.createCatalogMovieCard(movie, index);
            catalogGrid.appendChild(movieCard);
        });
        
        // Add staggered animation
        const cards = catalogGrid.querySelectorAll('.movie-card');
        cards.forEach((card, index) => {
            setTimeout(() => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(30px)';
                card.style.transition = 'all 0.6s ease';
                
                setTimeout(() => {
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, 50);
            }, index * 50);
        });
    }

    createCatalogMovieCard(movie, index) {
        const card = document.createElement('div');
        card.className = 'movie-card';
        
        const genres = Array.isArray(movie.genres) ? movie.genres.join(', ') : movie.genres || 'Unknown';
        const year = movie.year ? `(${movie.year})` : '';
        const rating = movie.avg_rating ? parseFloat(movie.avg_rating).toFixed(1) : 'N/A';
        const ratingCount = movie.rating_count ? `${movie.rating_count} ratings` : 'No ratings';
        
        // Generate star rating
        const stars = this.generateStarRating(movie.avg_rating || 0);
        
        // Popularity color
        const popularityColor = this.getPopularityColor(movie.popularity || 0);
        
        card.innerHTML = `
            <div class="movie-poster">
                🎬
                <div class="score-badge" style="position: absolute; top: 1rem; right: 1rem; background: ${popularityColor};">
                    ${movie.popularity ? movie.popularity.toFixed(1) : '0.0'}
                </div>
            </div>
            <div class="movie-info">
                <h3 class="movie-title">${movie.title} ${year}</h3>
                <div class="movie-genres">${genres}</div>
                <div class="movie-stats">
                    <div class="rating-stars">${stars}</div>
                    <div style="font-size: 0.8rem; color: var(--netflix-text-gray);">${rating} ⭐ ${ratingCount}</div>
                </div>
                <div style="margin-top: 1rem; font-size: 0.8rem; color: var(--netflix-text-gray);">
                    <div>📊 Popularity: ${movie.popularity ? movie.popularity.toFixed(1) : '0.0'}</div>
                    <div>🎬 Movie ID: ${movie.movie_id}</div>
                </div>
            </div>
        `;

        card.addEventListener('click', () => {
            this.showMovieDetails(movie);
        });

        return card;
    }

    getPopularityColor(popularity) {
        if (popularity >= 15) return 'var(--success-green)';
        if (popularity >= 10) return 'var(--warning-yellow)';
        if (popularity >= 5) return 'var(--info-blue)';
        return 'var(--netflix-red)';
    }

    displayCatalogPagination(pagination) {
        const paginationDiv = document.getElementById('catalog-pagination');
        
        if (pagination.total_pages <= 1) {
            paginationDiv.innerHTML = '';
            return;
        }
        
        let paginationHTML = '<div style="display: flex; gap: 0.5rem; justify-content: center; align-items: center;">';
        
        // Previous button
        if (pagination.has_prev) {
            paginationHTML += `<button class="btn btn-secondary" onclick="loadCatalog(${pagination.page - 1})">← Previous</button>`;
        }
        
        // Page numbers
        const startPage = Math.max(1, pagination.page - 2);
        const endPage = Math.min(pagination.total_pages, pagination.page + 2);
        
        if (startPage > 1) {
            paginationHTML += `<button class="btn btn-secondary" onclick="loadCatalog(1)">1</button>`;
            if (startPage > 2) {
                paginationHTML += '<span style="color: var(--netflix-text-gray);">...</span>';
            }
        }
        
        for (let i = startPage; i <= endPage; i++) {
            const isActive = i === pagination.page;
            const btnClass = isActive ? 'btn btn-primary' : 'btn btn-secondary';
            paginationHTML += `<button class="${btnClass}" onclick="loadCatalog(${i})">${i}</button>`;
        }
        
        if (endPage < pagination.total_pages) {
            if (endPage < pagination.total_pages - 1) {
                paginationHTML += '<span style="color: var(--netflix-text-gray);">...</span>';
            }
            paginationHTML += `<button class="btn btn-secondary" onclick="loadCatalog(${pagination.total_pages})">${pagination.total_pages}</button>`;
        }
        
        // Next button
        if (pagination.has_next) {
            paginationHTML += `<button class="btn btn-secondary" onclick="loadCatalog(${pagination.page + 1})">Next →</button>`;
        }
        
        paginationHTML += '</div>';
        paginationDiv.innerHTML = paginationHTML;
    }

    displayCatalogStats(pagination) {
        const statsDiv = document.getElementById('catalog-stats');
        const start = (pagination.page - 1) * pagination.per_page + 1;
        const end = Math.min(pagination.page * pagination.per_page, pagination.total_movies);
        
        statsDiv.innerHTML = `
            Showing ${start}-${end} of ${pagination.total_movies.toLocaleString()} movies 
            (Page ${pagination.page} of ${pagination.total_pages})
        `;
    }

    clearCatalogFilters() {
        document.getElementById('catalog-sort').value = 'popularity';
        document.getElementById('catalog-genre').value = '';
        document.getElementById('catalog-year-min').value = '';
        document.getElementById('catalog-year-max').value = '';
        document.getElementById('catalog-rating-min').value = '';
        
        // Reload catalog with cleared filters
        this.loadCatalog(1);
    }

    // Enhanced Catalog Functions
    debounceSearch(func, delay) {
        let timeoutId;
        return (...args) => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    }

    setupCatalogSearch() {
        const searchInput = document.getElementById('catalog-search');
        if (searchInput) {
            const debouncedSearch = this.debounceSearch(() => {
                this.filterCatalog();
            }, 300);
            
            searchInput.addEventListener('input', debouncedSearch);
        }
    }

    toggleAdvancedFilters() {
        const filtersPanel = document.getElementById('advanced-filters');
        const toggleBtn = document.querySelector('.filters-toggle');
        
        if (filtersPanel && toggleBtn) {
            if (filtersPanel.style.display === 'none' || !filtersPanel.style.display) {
                filtersPanel.style.display = 'block';
                toggleBtn.innerHTML = '🔽 Hide Advanced Filters';
            } else {
                filtersPanel.style.display = 'none';
                toggleBtn.innerHTML = '🔽 Show Advanced Filters';
            }
        }
    }

    quickGenreFilter(genre) {
        // Clear existing filters
        const elements = {
            search: document.getElementById('catalog-search'),
            genreSelect: document.getElementById('catalog-genre'),
            sort: document.getElementById('catalog-sort'),
            yearMin: document.getElementById('catalog-year-min'),
            yearMax: document.getElementById('catalog-year-max'),
            ratingMin: document.getElementById('catalog-rating-min')
        };

        if (elements.search) elements.search.value = '';
        if (elements.genreSelect) elements.genreSelect.value = genre;
        if (elements.sort) elements.sort.value = 'title';
        if (elements.yearMin) elements.yearMin.value = '';
        if (elements.yearMax) elements.yearMax.value = '';
        if (elements.ratingMin) elements.ratingMin.value = '';
        
        // Apply filter
        this.filterCatalog();
    }

    setView(viewType) {
        const catalogGrid = document.getElementById('catalog-movies');
        const viewButtons = document.querySelectorAll('.view-toggle button');
        
        if (catalogGrid) {
            // Update button states
            viewButtons.forEach(btn => btn.classList.remove('active'));
            const activeButton = document.querySelector(`button[onclick*="${viewType}"]`);
            if (activeButton) activeButton.classList.add('active');
            
            // Update grid class
            catalogGrid.className = `catalog-grid ${viewType}-view`;
        }
    }

    async filterCatalog() {
        const searchTerm = document.getElementById('catalog-search')?.value.toLowerCase() || '';
        const selectedGenre = document.getElementById('catalog-genre')?.value || '';
        const sortBy = document.getElementById('catalog-sort')?.value || '';
        const yearMin = document.getElementById('catalog-year-min')?.value || '';
        const yearMax = document.getElementById('catalog-year-max')?.value || '';
        const ratingMin = document.getElementById('catalog-rating-min')?.value || '';
        
        // Show loading
        this.showCatalogLoading();
        
        try {
            // Build query parameters
            const params = new URLSearchParams();
            if (searchTerm) params.append('search', searchTerm);
            if (selectedGenre) params.append('genre', selectedGenre);
            if (sortBy) params.append('sort', sortBy);
            if (yearMin) params.append('year_min', yearMin);
            if (yearMax) params.append('year_max', yearMax);
            if (ratingMin) params.append('rating_min', ratingMin);
            
            const response = await fetch(`${this.apiUrl}/catalog?${params.toString()}`);
            if (response.ok) {
                const data = await response.json();
                this.displayCatalogMovies(data.movies || []);
                this.updateCatalogStats(data.stats || {});
            } else {
                throw new Error('Failed to fetch catalog data');
            }
            
        } catch (error) {
            console.error('Error filtering catalog:', error);
            this.showError('Failed to filter movies. Please try again.');
        } finally {
            this.hideCatalogLoading();
        }
    }

    showCatalogLoading() {
        const loadingIndicator = document.getElementById('catalog-loading');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'flex';
        }
    }

    hideCatalogLoading() {
        const loadingIndicator = document.getElementById('catalog-loading');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
    }

    updateCatalogStats(stats) {
        const statsContainer = document.getElementById('catalog-statistics');
        if (statsContainer && stats) {
            statsContainer.innerHTML = `
                <div class="stat-item">
                    <span class="stat-number">${stats.total || 0}</span>
                    <span class="stat-label">Total Movies</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${stats.filtered || 0}</span>
                    <span class="stat-label">Showing</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${stats.avg_rating || 0}</span>
                    <span class="stat-label">Avg Rating</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${stats.year_range || 'N/A'}</span>
                    <span class="stat-label">Year Range</span>
                </div>
            `;
        }
    }
}

// Global functions for HTML onclick handlers
function scrollToPreferences() {
    document.getElementById('preferences').scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

function applyPreset(presetType) {
    window.recommender.applyPreset(presetType);
}

function applyMood(moodType) {
    window.recommender.applyMood(moodType);
}

// Enhanced catalog global functions
function toggleAdvancedFilters() {
    if (window.recommender) {
        window.recommender.toggleAdvancedFilters();
    }
}

function quickGenreFilter(genre) {
    if (window.recommender) {
        window.recommender.quickGenreFilter(genre);
    }
}

function setView(viewType) {
    if (window.recommender) {
        window.recommender.setView(viewType);
    }
}

function resetForm() {
    window.recommender.resetForm();
}

function exportResults() {
    window.recommender.exportResults();
}

function showCatalog() {
    window.recommender.showCatalog();
}

function loadCatalog(page) {
    window.recommender.loadCatalog(page);
}

function clearCatalogFilters() {
    window.recommender.clearCatalogFilters();
}

// Navigation functions
function showMetrics() {
    // Hide other sections
    document.getElementById('recommendations').style.display = 'none';
    document.getElementById('catalog-section').style.display = 'none';
    
    // Show metrics and load data
    window.recommender.loadMetrics();
}

function showAbout() {
    // Scroll to about section
    document.getElementById('about').scrollIntoView({
        behavior: 'smooth'
    });
}

function scrollToPreferences() {
    document.getElementById('preferences').scrollIntoView({
        behavior: 'smooth'
    });
}

// Update navigation event handlers
document.addEventListener('DOMContentLoaded', function() {
    // Add click handlers for navigation
    const navLinks = document.querySelectorAll('.nav-links a');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            if (href === '#metrics') {
                e.preventDefault();
                showMetrics();
            } else if (href === '#about') {
                e.preventDefault();
                showAbout();
            }
        });
    });
});

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    window.recommender = new NetflixMovieRecommender();
});



// Add some Netflix-style easter eggs
document.addEventListener('keydown', (e) => {
    // Konami code for fun
    if (e.code === 'KeyN' && e.ctrlKey && e.shiftKey) {
        document.body.style.filter = 'hue-rotate(180deg)';
        setTimeout(() => {
            document.body.style.filter = 'none';
        }, 2000);
    }
});
