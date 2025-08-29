/**
 * CineAI - Professional Movie Recommendation System
 * Enhanced frontend with advanced features and professional UI/UX
 */

// Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Global state
let currentRecommendations = [];
let isLoading = false;
let systemStatus = 'connecting';

// DOM Elements
const preferencesForm = document.getElementById('preferences-form');
const loadingSection = document.getElementById('loading-section');
const resultsSection = document.getElementById('results-section');
const errorSection = document.getElementById('error-section');
const recommendationsGrid = document.getElementById('recommendations-grid');
const resultsSummary = document.getElementById('results-summary');
const errorText = document.getElementById('error-text');
const movieModal = document.getElementById('movie-modal');
const sortSelect = document.getElementById('sort-select');
const apiStatus = document.getElementById('api-status');

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    console.log('🚀 Initializing CineAI Professional...');
    
    // Bind event listeners
    bindEventListeners();
    
    // Initialize preference sliders
    initializePreferenceSliders();
    
    // Check API health
    checkAPIHealth();
    
    // Set demo preferences
    loadActionPreset();
    
    console.log('✅ CineAI initialized successfully');
}

/**
 * Bind all event listeners
 */
function bindEventListeners() {
    // Form submission
    preferencesForm.addEventListener('submit', handleFormSubmit);
    
    // Sort functionality
    sortSelect.addEventListener('change', handleSortChange);
    
    // Modal close on outside click
    window.addEventListener('click', function(event) {
        if (event.target === movieModal) {
            closeMovieModal();
        }
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && movieModal.style.display === 'block') {
            closeMovieModal();
        }
        if (event.key === 'Enter' && event.ctrlKey) {
            handleFormSubmit(event);
        }
    });
}

/**
 * Initialize preference sliders with real-time updates
 */
function initializePreferenceSliders() {
    const sliders = document.querySelectorAll('.preference-slider');
    
    sliders.forEach(slider => {
        const valueDisplay = document.getElementById(slider.id.replace('-pref', '-value'));
        
        slider.addEventListener('input', function() {
            const value = parseInt(this.value);
            valueDisplay.textContent = value;
            
            // Update color based on value
            const hue = (value - 1) * 12; // 0-108 degrees (red to green)
            valueDisplay.style.backgroundColor = `hsl(${hue}, 70%, 50%)`;
        });
        
        // Initialize display
        slider.dispatchEvent(new Event('input'));
    });
}

/**
 * Check API health and update status
 */
async function checkAPIHealth() {
    try {
        updateSystemStatus('connecting', 'Connecting to AI system...');
        
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            updateSystemStatus('healthy', 'AI system online');
            console.log('✅ API is healthy:', data);
        } else {
            updateSystemStatus('warning', 'AI system degraded');
            console.warn('⚠️ API health check failed:', data);
        }
    } catch (error) {
        updateSystemStatus('error', 'AI system offline');
        console.error('❌ Failed to check API health:', error);
        showError('Unable to connect to the AI recommendation system. Please ensure the backend is running.');
    }
}

/**
 * Update system status indicator
 */
function updateSystemStatus(status, message) {
    systemStatus = status;
    const statusDot = apiStatus.querySelector('.status-dot');
    const statusText = apiStatus.querySelector('.status-text');
    
    statusDot.className = `status-dot status-${status}`;
    statusText.textContent = message;
}

/**
 * Handle form submission
 */
async function handleFormSubmit(event) {
    event.preventDefault();
    
    if (isLoading) return;
    
    try {
        // Collect and validate form data
        const formData = collectFormData();
        const validation = validateFormData(formData);
        
        if (!validation.isValid) {
            showError(validation.message);
            return;
        }
        
        // Show loading state
        showLoading();
        
        // Get recommendations
        const recommendations = await getRecommendations(formData);
        
        // Display results
        displayRecommendations(recommendations, formData);
        
        // Track analytics
        trackRecommendationRequest(formData, recommendations);
        
    } catch (error) {
        console.error('❌ Error getting recommendations:', error);
        showError(`Failed to get recommendations: ${error.message}`);
    } finally {
        hideLoading();
    }
}

/**
 * Collect form data with enhanced processing
 */
function collectFormData() {
    const user_preferences = {};
    
    // Collect genre preferences from sliders
    const sliders = document.querySelectorAll('.preference-slider');
    sliders.forEach(slider => {
        const genreName = slider.name.replace('-pref', '');
        const capitalizedGenre = genreName.charAt(0).toUpperCase() + genreName.slice(1);
        user_preferences[capitalizedGenre] = parseInt(slider.value);
    });
    
    // Collect other form data
    const watchedMoviesText = document.getElementById('watched-movies').value;
    const topK = parseInt(document.getElementById('top-k').value);
    
    // Parse watched movies with better processing
    const watched_movies = watchedMoviesText
        .split(/[,\n]/)
        .map(movie => movie.trim())
        .filter(movie => movie.length > 0)
        .map(movie => movie.replace(/[^\w\s]/gi, '').trim()); // Clean special characters
    
    return {
        user_preferences: user_preferences,
        watched_movies: watched_movies,
        top_k: topK
    };
}

/**
 * Enhanced form validation
 */
function validateFormData(formData) {
    // Check if preferences are set
    const preferences = formData.user_preferences;
    const hasPreferences = Object.keys(preferences).length > 0;
    
    if (!hasPreferences) {
        return {
            isValid: false,
            message: 'Please set your genre preferences using the sliders above.'
        };
    }
    
    // Check if all preferences are at default (5)
    const allDefault = Object.values(preferences).every(val => val === 5);
    if (allDefault) {
        return {
            isValid: false,
            message: 'Please adjust at least one genre preference to get personalized recommendations.'
        };
    }
    
    // Validate top_k
    if (formData.top_k < 1 || formData.top_k > 50) {
        return {
            isValid: false,
            message: 'Number of recommendations must be between 1 and 50.'
        };
    }
    
    return { isValid: true };
}

/**
 * Get recommendations from API with retry logic
 */
async function getRecommendations(formData, retries = 3) {
    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            const response = await fetch(`${API_BASE_URL}/user/preferences`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }
            
            return await response.json();
            
        } catch (error) {
            console.warn(`⚠️ Attempt ${attempt} failed:`, error.message);
            
            if (attempt === retries) {
                throw error;
            }
            
            // Wait before retry
            await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
        }
    }
}

/**
 * Display recommendations with enhanced UI
 */
function displayRecommendations(data, formData) {
    currentRecommendations = data.recommendations || [];
    
    // Update results summary with rich information
    const totalCandidates = data.total_movies_considered || 0;
    const processingTime = data.processing_time || 0;
    
    resultsSummary.innerHTML = `
        <div class="summary-stats">
            <div class="stat-item">
                <span class="stat-number">${currentRecommendations.length}</span>
                <span class="stat-label">Recommendations</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">${totalCandidates.toLocaleString()}</span>
                <span class="stat-label">Movies Analyzed</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">${processingTime.toFixed(2)}s</span>
                <span class="stat-label">Processing Time</span>
            </div>
        </div>
    `;
    
    // Clear and populate recommendations grid
    recommendationsGrid.innerHTML = '';
    
    if (currentRecommendations.length === 0) {
        showNoResults();
        return;
    }
    
    // Create movie cards with staggered animation
    currentRecommendations.forEach((movie, index) => {
        const movieCard = createEnhancedMovieCard(movie, index + 1);
        movieCard.style.animationDelay = `${index * 0.1}s`;
        recommendationsGrid.appendChild(movieCard);
    });
    
    // Show results section
    hideAllSections();
    resultsSection.style.display = 'block';
    resultsSection.classList.add('fade-in');
    
    // Smooth scroll to results
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 300);
}

/**
 * Create enhanced movie card with professional styling
 */
function createEnhancedMovieCard(movie, rank) {
    const card = document.createElement('div');
    card.className = 'movie-card slide-up';
    
    // Format data
    const title = movie.title || 'Unknown Movie';
    const year = movie.year || 'Unknown';
    const genres = movie.genres || [];
    const finalScore = parseFloat(movie.final_score || 0);
    const fuzzyScore = parseFloat(movie.fuzzy_score || 0);
    const annScore = parseFloat(movie.ann_score || 0);
    const explanation = movie.explanation || 'No explanation available';
    
    // Generate genres HTML
    const genresHtml = genres
        .map(genre => `<span class="genre-tag">${genre}</span>`)
        .join('');
    
    // Score color based on value
    const getScoreColor = (score) => {
        if (score >= 8) return '#48bb78';
        if (score >= 6) return '#ed8936';
        if (score >= 4) return '#e53e3e';
        return '#718096';
    };
    
    // Popularity indicator
    const popularity = movie.popularity || 50;
    const popularityStars = '⭐'.repeat(Math.round(popularity / 20));
    
    card.innerHTML = `
        <div class="movie-card-header">
            <div class="movie-title">${title}</div>
            <div class="movie-year">${year}</div>
            <div class="movie-score" style="background-color: ${getScoreColor(finalScore)}">
                ${finalScore.toFixed(1)}
            </div>
        </div>
        
        <div class="movie-card-body">
            <div class="movie-genres">
                ${genresHtml}
            </div>
            
            <div class="movie-popularity">
                <span class="popularity-label">Popularity:</span>
                <span class="popularity-stars">${popularityStars}</span>
                <span class="popularity-score">${popularity.toFixed(0)}/100</span>
            </div>
            
            <div class="movie-scores">
                <div class="score-item">
                    <div class="score-label">🧠 Fuzzy Logic</div>
                    <div class="score-value">${fuzzyScore.toFixed(1)}</div>
                </div>
                <div class="score-item">
                    <div class="score-label">🤖 Neural Net</div>
                    <div class="score-value">${annScore.toFixed(1)}</div>
                </div>
            </div>
            
            <div class="movie-explanation">
                <strong>Why recommended:</strong> ${explanation}
            </div>
            
            <div class="movie-actions">
                <button class="action-btn" onclick="showMovieDetails(${movie.movie_id})">
                    📋 Details
                </button>
                <button class="action-btn" onclick="explainRecommendation(${movie.movie_id})">
                    🤔 Explain
                </button>
                <button class="action-btn" onclick="addToWatchlist(${movie.movie_id})">
                    ➕ Watchlist
                </button>
            </div>
        </div>
    `;
    
    // Add click handler
    card.addEventListener('click', (e) => {
        if (!e.target.classList.contains('action-btn')) {
            showMovieDetails(movie.movie_id);
        }
    });
    
    return card;
}

/**
 * Handle sort change
 */
function handleSortChange() {
    const sortBy = sortSelect.value;
    
    if (!currentRecommendations.length) return;
    
    // Sort recommendations
    const sorted = [...currentRecommendations].sort((a, b) => {
        switch (sortBy) {
            case 'fuzzy':
                return b.fuzzy_score - a.fuzzy_score;
            case 'ann':
                return b.ann_score - a.ann_score;
            case 'title':
                return (a.title || '').localeCompare(b.title || '');
            case 'year':
                return (b.year || 0) - (a.year || 0);
            default: // score
                return b.final_score - a.final_score;
        }
    });
    
    // Re-render grid
    recommendationsGrid.innerHTML = '';
    sorted.forEach((movie, index) => {
        const movieCard = createEnhancedMovieCard(movie, index + 1);
        movieCard.style.animationDelay = `${index * 0.05}s`;
        recommendationsGrid.appendChild(movieCard);
    });
}

/**
 * Show enhanced movie details modal
 */
async function showMovieDetails(movieId) {
    try {
        const response = await fetch(`${API_BASE_URL}/movie/${movieId}`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch movie details');
        }
        
        const movie = await response.json();
        const recommendedMovie = currentRecommendations.find(m => m.movie_id === movieId);
        
        const modalTitle = document.getElementById('modal-title');
        const modalContent = document.getElementById('movie-details');
        
        modalTitle.textContent = movie.title || 'Movie Details';
        
        modalContent.innerHTML = `
            <div class="movie-detail-grid">
                <div class="detail-section">
                    <h3>📽️ Basic Information</h3>
                    <div class="detail-item">
                        <span class="detail-label">Title:</span>
                        <span class="detail-value">${movie.title || 'Unknown'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Year:</span>
                        <span class="detail-value">${movie.year || 'Unknown'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Genres:</span>
                        <span class="detail-value">${(movie.genres || []).join(', ')}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Popularity:</span>
                        <span class="detail-value">${movie.popularity ? movie.popularity.toFixed(1) + '/100' : 'Unknown'}</span>
                    </div>
                </div>
                
                ${recommendedMovie ? `
                <div class="detail-section">
                    <h3>🎯 AI Recommendation Analysis</h3>
                    <div class="score-breakdown">
                        <div class="score-bar">
                            <span class="score-label">Final Score</span>
                            <div class="score-progress">
                                <div class="score-fill" style="width: ${recommendedMovie.final_score * 10}%"></div>
                            </div>
                            <span class="score-number">${recommendedMovie.final_score.toFixed(1)}/10</span>
                        </div>
                        <div class="score-bar">
                            <span class="score-label">🧠 Fuzzy Logic</span>
                            <div class="score-progress">
                                <div class="score-fill fuzzy" style="width: ${recommendedMovie.fuzzy_score * 10}%"></div>
                            </div>
                            <span class="score-number">${recommendedMovie.fuzzy_score.toFixed(1)}/10</span>
                        </div>
                        <div class="score-bar">
                            <span class="score-label">🤖 Neural Network</span>
                            <div class="score-progress">
                                <div class="score-fill neural" style="width: ${recommendedMovie.ann_score * 10}%"></div>
                            </div>
                            <span class="score-number">${recommendedMovie.ann_score.toFixed(1)}/10</span>
                        </div>
                    </div>
                    
                    <div class="explanation-box">
                        <h4>🤔 Why This Movie?</h4>
                        <p>${recommendedMovie.explanation}</p>
                    </div>
                </div>
                ` : ''}
            </div>
        `;
        
        movieModal.style.display = 'block';
        
    } catch (error) {
        console.error('❌ Error fetching movie details:', error);
        showError('Failed to load movie details');
    }
}

/**
 * Preset functions for quick setup
 */
function loadActionPreset() {
    setPreferences({ Action: 9, Adventure: 8, Thriller: 7, Scifi: 6, Drama: 4, Comedy: 3, Romance: 2, Horror: 3 });
    document.getElementById('watched-movies').value = 'The Dark Knight, Mad Max: Fury Road, John Wick, Mission Impossible';
}

function loadComedyPreset() {
    setPreferences({ Comedy: 9, Romance: 7, Adventure: 6, Drama: 5, Action: 4, Scifi: 3, Thriller: 2, Horror: 1 });
    document.getElementById('watched-movies').value = 'The Hangover, Superbad, Anchorman, Dumb and Dumber';
}

function loadDramaPreset() {
    setPreferences({ Drama: 9, Romance: 7, Thriller: 6, Action: 4, Comedy: 4, Adventure: 3, Scifi: 3, Horror: 2 });
    document.getElementById('watched-movies').value = 'The Shawshank Redemption, Forrest Gump, Titanic, A Beautiful Mind';
}

function loadSciFiPreset() {
    setPreferences({ Scifi: 9, Action: 8, Adventure: 7, Thriller: 6, Drama: 5, Comedy: 3, Romance: 2, Horror: 4 });
    document.getElementById('watched-movies').value = 'Interstellar, Blade Runner 2049, The Matrix, Star Wars';
}

function resetPreferences() {
    setPreferences({ Action: 5, Comedy: 5, Drama: 5, Horror: 5, Romance: 5, Scifi: 5, Thriller: 5, Adventure: 5 });
    document.getElementById('watched-movies').value = '';
}

function setPreferences(prefs) {
    Object.entries(prefs).forEach(([genre, value]) => {
        const slider = document.getElementById(`${genre.toLowerCase()}-pref`);
        if (slider) {
            slider.value = value;
            slider.dispatchEvent(new Event('input'));
        }
    });
}

/**
 * Utility functions
 */
function showLoading() {
    isLoading = true;
    hideAllSections();
    loadingSection.style.display = 'block';
    
    // Animate loading steps
    const steps = loadingSection.querySelectorAll('.loading-step');
    steps.forEach((step, index) => {
        setTimeout(() => {
            step.classList.add('active');
        }, index * 1000);
    });
    
    // Disable form
    const submitBtn = preferencesForm.querySelector('.recommend-btn');
    submitBtn.disabled = true;
    submitBtn.querySelector('.btn-text').style.display = 'none';
    submitBtn.querySelector('.btn-loader').style.display = 'inline';
}

function hideLoading() {
    isLoading = false;
    loadingSection.style.display = 'none';
    
    // Re-enable form
    const submitBtn = preferencesForm.querySelector('.recommend-btn');
    submitBtn.disabled = false;
    submitBtn.querySelector('.btn-text').style.display = 'inline';
    submitBtn.querySelector('.btn-loader').style.display = 'none';
}

function showError(message) {
    hideAllSections();
    errorText.textContent = message;
    errorSection.style.display = 'block';
    errorSection.scrollIntoView({ behavior: 'smooth' });
}

function hideError() {
    errorSection.style.display = 'none';
}

function hideAllSections() {
    loadingSection.style.display = 'none';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
}

function closeMovieModal() {
    movieModal.style.display = 'none';
}

function showNoResults() {
    recommendationsGrid.innerHTML = `
        <div class="no-results">
            <div class="no-results-icon">🎬</div>
            <h3>No recommendations found</h3>
            <p>Try adjusting your preferences or reducing the number of watched movies.</p>
            <button class="btn btn-primary" onclick="resetPreferences()">Reset Preferences</button>
        </div>
    `;
}

// Additional utility functions
function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function exportResults() {
    if (!currentRecommendations.length) return;
    
    const csv = [
        ['Rank', 'Title', 'Year', 'Genres', 'Final Score', 'Fuzzy Score', 'Neural Score', 'Explanation'],
        ...currentRecommendations.map((movie, index) => [
            index + 1,
            movie.title || '',
            movie.year || '',
            (movie.genres || []).join('; '),
            movie.final_score || '',
            movie.fuzzy_score || '',
            movie.ann_score || '',
            movie.explanation || ''
        ])
    ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cineai-recommendations-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
}

function getMoreRecommendations() {
    const topKSelect = document.getElementById('top-k');
    const currentValue = parseInt(topKSelect.value);
    const newValue = Math.min(currentValue + 5, 50);
    topKSelect.value = newValue;
    
    handleFormSubmit(new Event('submit'));
}

function addToWatchlist(movieId) {
    // Mock watchlist functionality
    const movie = currentRecommendations.find(m => m.movie_id === movieId);
    if (movie) {
        alert(`Added "${movie.title}" to your watchlist! 🎬`);
        // In a real app, this would save to user's account
    }
}

function trackRecommendationRequest(formData, recommendations) {
    // Mock analytics tracking
    console.log('📊 Analytics:', {
        preferences: formData.user_preferences,
        watchedCount: formData.watched_movies.length,
        recommendationsCount: recommendations.recommendations?.length || 0,
        timestamp: new Date().toISOString()
    });
}

// Export functions for global access
window.showMovieDetails = showMovieDetails;
window.explainRecommendation = showMovieDetails; // Same function for now
window.closeMovieModal = closeMovieModal;
window.hideError = hideError;
window.loadActionPreset = loadActionPreset;
window.loadComedyPreset = loadComedyPreset;
window.loadDramaPreset = loadDramaPreset;
window.loadSciFiPreset = loadSciFiPreset;
window.resetPreferences = resetPreferences;
window.scrollToTop = scrollToTop;
window.exportResults = exportResults;
window.getMoreRecommendations = getMoreRecommendations;
window.addToWatchlist = addToWatchlist;

console.log('🎬 CineAI Professional frontend loaded successfully!');
