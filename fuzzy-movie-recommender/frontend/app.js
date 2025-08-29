/**
 * Fuzzy Movie Recommender - Frontend JavaScript
 * 
 * This file handles all frontend interactions including:
 * - Form submission and validation
 * - API communication
 * - Results display and formatting
 * - Movie detail modals
 * - Error handling
 */

// Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Global state
let currentRecommendations = [];
let isLoading = false;

// DOM Elements
const preferencesForm = document.getElementById('preferences-form');
const loadingSection = document.getElementById('loading-section');
const resultsSection = document.getElementById('results-section');
const errorSection = document.getElementById('error-section');
const recommendationsGrid = document.getElementById('recommendations-grid');
const resultsSummary = document.getElementById('results-summary');
const errorText = document.getElementById('error-text');
const movieModal = document.getElementById('movie-modal');

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    console.log('Initializing Fuzzy Movie Recommender...');
    
    // Bind event listeners
    preferencesForm.addEventListener('submit', handleFormSubmit);
    
    // Check API health
    checkAPIHealth();
    
    // Set default preferences for demo
    setDefaultPreferences();
    
    console.log('App initialized successfully');
}

/**
 * Set default preferences for better demo experience
 */
function setDefaultPreferences() {
    document.getElementById('action-pref').value = 'High';
    document.getElementById('comedy-pref').value = 'Medium';
    document.getElementById('romance-pref').value = 'Low';
    document.getElementById('thriller-pref').value = 'High';
    document.getElementById('scifi-pref').value = 'Very High';
    document.getElementById('drama-pref').value = 'Medium';
    document.getElementById('horror-pref').value = 'Very Low';
    document.getElementById('animation-pref').value = 'Low';
    
    // Set some example watched movies
    document.getElementById('watched-movies').value = 'The Dark Knight, Inception, Titanic';
}

/**
 * Check if the API is healthy
 */
async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            console.log('API is healthy:', data);
        } else {
            console.warn('API health check failed:', data);
        }
    } catch (error) {
        console.error('Failed to check API health:', error);
        showError('Unable to connect to the recommendation server. Please make sure the backend is running.');
    }
}

/**
 * Handle form submission
 */
async function handleFormSubmit(event) {
    event.preventDefault();
    
    if (isLoading) {
        return;
    }
    
    try {
        // Collect form data
        const formData = collectFormData();
        
        // Validate form data
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
        
    } catch (error) {
        console.error('Error getting recommendations:', error);
        showError('Failed to get recommendations. Please try again.');
    } finally {
        hideLoading();
    }
}

/**
 * Collect form data
 */
function collectFormData() {
    const user_preferences = {};
    
    // Map text values to numbers for backend
    const valueMap = {
        'Very Low': 1,
        'Low': 3,
        'Medium': 5,
        'High': 7,
        'Very High': 9
    };
    
    // Collect genre preferences
    const genreSelects = preferencesForm.querySelectorAll('select[name]');
    genreSelects.forEach(select => {
        const genreName = select.name.replace('-pref', '');
        const capitalizedGenre = genreName.charAt(0).toUpperCase() + genreName.slice(1);
        user_preferences[capitalizedGenre] = valueMap[select.value] || 5;
    });
    
    // Collect other form data
    const userId = document.getElementById('user-id').value;
    const watchedMoviesText = document.getElementById('watched-movies').value;
    const topK = parseInt(document.getElementById('top-k').value);
    
    // Parse watched movies
    const watched_movies = watchedMoviesText
        .split(',')
        .map(movie => movie.trim())
        .filter(movie => movie.length > 0);
    
    return {
        user_preferences: user_preferences,
        watched_movies: watched_movies,
        top_k: topK
    };
}

/**
 * Validate form data
 */
function validateFormData(formData) {
    // Check if at least one preference is set
    const hasPreferences = Object.keys(formData.user_preferences).length > 0;
    if (!hasPreferences) {
        return {
            isValid: false,
            message: 'Please set at least one genre preference.'
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
 * Get recommendations from API
 */
async function getRecommendations(formData) {
    const response = await fetch(`${API_BASE_URL}/user/preferences`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    });
    
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to get recommendations');
    }
    
    return await response.json();
}

/**
 * Display recommendations
 */
function displayRecommendations(data, formData) {
    currentRecommendations = data.recommendations || [];
    
    // Update results summary
    const totalCandidates = data.total_movies_considered || 0;
    const watchedCount = data.watched_count || 0;
    
    resultsSummary.innerHTML = `
        Found <strong>${currentRecommendations.length}</strong> personalized recommendations
        from <strong>${totalCandidates}</strong> movies
        ${watchedCount > 0 ? `(excluding ${watchedCount} movies you've watched)` : ''}
    `;
    
    // Clear previous results
    recommendationsGrid.innerHTML = '';
    
    // Create movie cards
    currentRecommendations.forEach((movie, index) => {
        const movieCard = createMovieCard(movie, index + 1);
        recommendationsGrid.appendChild(movieCard);
    });
    
    // Show results section with animation
    hideAllSections();
    resultsSection.style.display = 'block';
    resultsSection.classList.add('fade-in');
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Create a movie card element
 */
function createMovieCard(movie, rank) {
    const card = document.createElement('div');
    card.className = 'movie-card slide-up';
    card.style.animationDelay = `${rank * 0.1}s`;
    
    // Format genres
    const genresHtml = (movie.genres || [])
        .map(genre => `<span class="genre-tag">${genre}</span>`)
        .join('');
    
    // Format scores
    const finalScore = parseFloat(movie.final_score || 0).toFixed(1);
    const fuzzyScore = parseFloat(movie.fuzzy_score || 0).toFixed(1);
    const annScore = parseFloat(movie.ann_score || 0).toFixed(1);
    
    // Get score color based on value
    const getScoreColor = (score) => {
        if (score >= 8) return '#27ae60';
        if (score >= 6) return '#f39c12';
        if (score >= 4) return '#e67e22';
        return '#e74c3c';
    };
    
    card.innerHTML = `
        <div class="movie-header">
            <h3 class="movie-title">${movie.title || 'Unknown Movie'}</h3>
            <div class="movie-score" style="background-color: ${getScoreColor(finalScore)}">
                ${finalScore}/10
            </div>
        </div>
        
        <div class="movie-genres">
            ${genresHtml}
        </div>
        
        <div class="movie-scores">
            <div class="score-item">
                <div class="score-label">Fuzzy Logic</div>
                <div class="score-value">${fuzzyScore}</div>
            </div>
            <div class="score-item">
                <div class="score-label">Neural Network</div>
                <div class="score-value">${annScore}</div>
            </div>
        </div>
        
        <div class="movie-explanation">
            ${movie.explanation || 'No explanation available'}
        </div>
        
        <div class="movie-actions">
            <button class="action-btn" onclick="showMovieDetails(${movie.movie_id})">
                📋 Details
            </button>
            <button class="action-btn" onclick="explainRecommendation(${movie.movie_id})">
                🤔 Why?
            </button>
        </div>
    `;
    
    // Add click handler for card
    card.addEventListener('click', (e) => {
        if (!e.target.classList.contains('action-btn')) {
            showMovieDetails(movie.movie_id);
        }
    });
    
    return card;
}

/**
 * Show movie details in modal
 */
async function showMovieDetails(movieId) {
    try {
        const response = await fetch(`${API_BASE_URL}/movie/${movieId}`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch movie details');
        }
        
        const movie = await response.json();
        
        // Find the movie in current recommendations for additional info
        const recommendedMovie = currentRecommendations.find(m => m.movie_id === movieId);
        
        const modalContent = document.getElementById('movie-details');
        modalContent.innerHTML = `
            <h2>${movie.title}</h2>
            
            <div class="movie-info-grid">
                <div class="info-section">
                    <h3>Basic Information</h3>
                    <p><strong>Year:</strong> ${movie.year || 'Unknown'}</p>
                    <p><strong>Genres:</strong> ${(movie.genres || []).join(', ')}</p>
                    <p><strong>Popularity:</strong> ${movie.popularity ? movie.popularity.toFixed(1) + '/100' : 'Unknown'}</p>
                    ${movie.avg_rating ? `<p><strong>Average Rating:</strong> ${movie.avg_rating}/5</p>` : ''}
                    ${movie.rating_count ? `<p><strong>Total Ratings:</strong> ${movie.rating_count}</p>` : ''}
                </div>
                
                ${recommendedMovie ? `
                <div class="info-section">
                    <h3>Recommendation Scores</h3>
                    <p><strong>Final Score:</strong> ${recommendedMovie.final_score}/10</p>
                    <p><strong>Fuzzy Logic Score:</strong> ${recommendedMovie.fuzzy_score}/10</p>
                    <p><strong>Neural Network Score:</strong> ${recommendedMovie.ann_score}/10</p>
                </div>
                
                <div class="info-section">
                    <h3>Explanation</h3>
                    <p>${recommendedMovie.explanation}</p>
                </div>
                ` : ''}
            </div>
        `;
        
        movieModal.style.display = 'block';
        
    } catch (error) {
        console.error('Error fetching movie details:', error);
        showError('Failed to load movie details');
    }
}

/**
 * Explain recommendation in detail
 */
function explainRecommendation(movieId) {
    const movie = currentRecommendations.find(m => m.movie_id === movieId);
    
    if (!movie) {
        showError('Movie not found in current recommendations');
        return;
    }
    
    const modalContent = document.getElementById('movie-details');
    modalContent.innerHTML = `
        <h2>Why "${movie.title}" was recommended</h2>
        
        <div class="explanation-details">
            <div class="explanation-section">
                <h3>🧠 Fuzzy Logic Analysis</h3>
                <p><strong>Score:</strong> ${movie.fuzzy_score}/10</p>
                <p>The fuzzy logic system analyzed your genre preferences and movie characteristics using human-like reasoning rules.</p>
            </div>
            
            <div class="explanation-section">
                <h3>🤖 Neural Network Analysis</h3>
                <p><strong>Score:</strong> ${movie.ann_score}/10</p>
                <p>The neural network learned patterns from similar users' preferences and predicted your likely rating.</p>
            </div>
            
            <div class="explanation-section">
                <h3>🎯 Combined Result</h3>
                <p><strong>Final Score:</strong> ${movie.final_score}/10</p>
                <p>${movie.explanation}</p>
            </div>
            
            <div class="explanation-section">
                <h3>📊 Movie Details</h3>
                <p><strong>Genres:</strong> ${(movie.genres || []).join(', ')}</p>
                <p><strong>Popularity:</strong> ${movie.popularity ? movie.popularity.toFixed(1) + '/100' : 'Unknown'}</p>
            </div>
        </div>
    `;
    
    movieModal.style.display = 'block';
}

/**
 * Close movie modal
 */
function closeMovieModal() {
    movieModal.style.display = 'none';
}

/**
 * Show loading state
 */
function showLoading() {
    isLoading = true;
    hideAllSections();
    loadingSection.style.display = 'block';
    
    // Disable form
    const submitBtn = preferencesForm.querySelector('.recommend-btn');
    submitBtn.disabled = true;
    submitBtn.querySelector('.btn-text').style.display = 'none';
    submitBtn.querySelector('.btn-loader').style.display = 'inline';
}

/**
 * Hide loading state
 */
function hideLoading() {
    isLoading = false;
    loadingSection.style.display = 'none';
    
    // Re-enable form
    const submitBtn = preferencesForm.querySelector('.recommend-btn');
    submitBtn.disabled = false;
    submitBtn.querySelector('.btn-text').style.display = 'inline';
    submitBtn.querySelector('.btn-loader').style.display = 'none';
}

/**
 * Show error message
 */
function showError(message) {
    hideAllSections();
    errorText.textContent = message;
    errorSection.style.display = 'block';
    errorSection.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Hide error message
 */
function hideError() {
    errorSection.style.display = 'none';
}

/**
 * Hide all sections
 */
function hideAllSections() {
    loadingSection.style.display = 'none';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
}

/**
 * Handle click outside modal to close it
 */
window.addEventListener('click', function(event) {
    if (event.target === movieModal) {
        closeMovieModal();
    }
});

/**
 * Handle escape key to close modal
 */
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && movieModal.style.display === 'block') {
        closeMovieModal();
    }
});

/**
 * Utility function to format numbers
 */
function formatNumber(num, decimals = 1) {
    return parseFloat(num).toFixed(decimals);
}

/**
 * Utility function to capitalize first letter
 */
function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Add some demo functionality
 */
function loadDemoPreferences() {
    // Action movie lover
    document.getElementById('action-pref').value = 'Very High';
    document.getElementById('thriller-pref').value = 'High';
    document.getElementById('scifi-pref').value = 'High';
    document.getElementById('comedy-pref').value = 'Low';
    document.getElementById('romance-pref').value = 'Very Low';
    document.getElementById('drama-pref').value = 'Medium';
    document.getElementById('horror-pref').value = 'Low';
    document.getElementById('animation-pref').value = 'Very Low';
    
    document.getElementById('watched-movies').value = 'Avengers, Fast & Furious, Mission Impossible';
}

// Export functions for global access
window.showMovieDetails = showMovieDetails;
window.explainRecommendation = explainRecommendation;
window.closeMovieModal = closeMovieModal;
window.hideError = hideError;
window.loadDemoPreferences = loadDemoPreferences;

console.log('Fuzzy Movie Recommender frontend loaded successfully!');
