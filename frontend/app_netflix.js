/**
 * Netflix-Style Movie Recommender Frontend
 * Enhanced UI with smooth animations and professional interactions
 */

class NetflixMovieRecommender {
    constructor() {
        this.apiUrl = 'http://127.0.0.1:3000';
        this.currentRecommendations = [];
        this.isLoading = false;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupSliders();
        this.checkSystemHealth();
        this.setupScrollEffects();
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
                valueDisplay.textContent = slider.value;
                this.updateSliderColor(slider);
            });

            // Initialize color
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
            action: { action: 9, thriller: 8, scifi: 7, drama: 4, comedy: 3, romance: 2, horror: 5, fantasy: 6 },
            comedy: { comedy: 9, romance: 7, drama: 5, action: 4, scifi: 3, thriller: 2, horror: 1, fantasy: 4 },
            drama: { drama: 9, romance: 7, thriller: 6, action: 4, comedy: 5, scifi: 3, horror: 2, fantasy: 4 },
            scifi: { scifi: 9, action: 8, thriller: 7, fantasy: 6, drama: 4, comedy: 3, romance: 2, horror: 5 },
            horror: { horror: 9, thriller: 8, action: 6, scifi: 5, drama: 3, comedy: 2, romance: 1, fantasy: 7 },
            romance: { romance: 9, drama: 8, comedy: 7, fantasy: 5, action: 3, thriller: 2, scifi: 2, horror: 1 }
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

    async getRecommendations() {
        if (this.isLoading) return;

        this.isLoading = true;
        this.showLoading(true);
        this.hideError();

        try {
            const requestData = this.prepareEnhancedRecommendationRequest();
            
            const response = await fetch(`${this.apiUrl}/recommend/enhanced`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (data.detail) {
                throw new Error(data.detail);
            }

            this.currentRecommendations = data.recommendations || [];
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
            this.showError(`Failed to get recommendations: ${error.message}`);
        } finally {
            this.isLoading = false;
            this.showLoading(false);
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
        
        return {
            user_preferences: userPreferences,
            num_recommendations: numRecommendations
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
            top_k: Math.min(numRecommendations, 50)
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
        const predictedRating = movie.predicted_rating || movie.hybrid_score || 0;
        const confidence = movie.confidence || (movie.agreement || 0);
        const imdbRating = movie.rating || movie.avg_rating || 0;
        
        // Generate star rating based on predicted score
        const stars = this.generateStarRating(predictedRating);
        
        // Score colors
        const scoreColor = this.getScoreColor(predictedRating);
        const confidenceColor = confidence > 0.8 ? '#46d369' : confidence > 0.6 ? '#f5c842' : '#E50914';
        
        card.innerHTML = `
            <div class="movie-poster-container">
                <div class="movie-rank">#${index + 1}</div>
                <img class="movie-poster-img" src="${posterUrl}" alt="${title}" loading="lazy"
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
                    <div style="font-size: 1.5rem; font-weight: 600; color: var(--netflix-red);">${(movie.score || 0).toFixed(1)}</div>
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
