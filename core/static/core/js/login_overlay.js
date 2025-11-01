/**
 * Login Overlay Controller
 * Handles slide in/out animations and HTMX integration
 */

class LoginOverlay {
    constructor() {
        this.overlay = null;
        this.form = null;
        this.isAnimating = false;
        this.init();
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        this.overlay = document.getElementById('login-overlay');
        if (!this.overlay) {
            console.log('LOGIN DEBUG: No overlay element found');
            return;
        }

        this.form = this.overlay.querySelector('#login-form');
        this.setupEventListeners();
        
        // Debug authentication detection
        console.log('LOGIN DEBUG: Body classes:', document.body.className);
        console.log('LOGIN DEBUG: Meta tag content:', document.querySelector('meta[name="user-authenticated"]')?.content);
        console.log('LOGIN DEBUG: Is authenticated:', this.isUserAuthenticated());
        
        // Show overlay if user is not authenticated
        if (!this.isUserAuthenticated()) {
            console.log('LOGIN DEBUG: Showing overlay for unauthenticated user');
            this.show();
        } else {
            console.log('LOGIN DEBUG: User is authenticated, not showing overlay');
        }
    }

    setupEventListeners() {
        // Handle form submission
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }

        // Handle HTMX responses
        document.addEventListener('htmx:responseError', (e) => this.handleLoginError(e));
        document.addEventListener('htmx:afterRequest', (e) => this.handleLoginResponse(e));

        // Handle escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isVisible()) {
                this.hide();
            }
        });

        // Prevent body scroll when overlay is visible
        this.overlay.addEventListener('transitionstart', () => {
            if (this.isVisible()) {
                document.body.style.overflow = 'hidden';
            }
        });

        this.overlay.addEventListener('transitionend', () => {
            if (!this.isVisible()) {
                document.body.style.overflow = '';
            }
            this.isAnimating = false;
        });
    }

    isUserAuthenticated() {
        // Check if user is authenticated (can be customized based on your auth logic)
        return document.body.classList.contains('authenticated') || 
               document.querySelector('meta[name="user-authenticated"]')?.content === 'true';
    }

    isVisible() {
        return this.overlay && this.overlay.classList.contains('show');
    }

    show() {
        if (!this.overlay || this.isVisible() || this.isAnimating) return;
        
        this.isAnimating = true;
        this.overlay.classList.remove('hide');
        this.overlay.classList.add('show');
        
        // Focus on first input field after animation
        setTimeout(() => {
            const firstInput = this.overlay.querySelector('.input-field');
            if (firstInput) firstInput.focus();
        }, 500);
    }

    hide() {
        if (!this.overlay || !this.isVisible() || this.isAnimating) return;
        
        this.isAnimating = true;
        this.overlay.classList.remove('show');
        this.overlay.classList.add('hide');
    }

    handleFormSubmit(event) {
        const button = this.form.querySelector('.login-button');
        const buttonText = button.querySelector('.button-text');
        const spinner = button.querySelector('.loading-spinner');
        
        // Show loading state
        button.disabled = true;
        buttonText.style.opacity = '0';
        spinner.style.display = 'block';
    }

    handleLoginError(event) {
        if (event.target.closest('#login-form')) {
            const formContainer = this.overlay.querySelector('.login-form-container');
            const button = this.form.querySelector('.login-button');
            const buttonText = button.querySelector('.button-text');
            const spinner = button.querySelector('.loading-spinner');
            
            // Reset button state
            button.disabled = false;
            buttonText.style.opacity = '1';
            spinner.style.display = 'none';
            
            // Add error animation
            formContainer.classList.add('error');
            setTimeout(() => {
                formContainer.classList.remove('error');
            }, 500);
            
            // Show error message
            this.showErrorMessage('Invalid credentials. Please try again.');
        }
    }

    handleLoginResponse(event) {
        if (event.target.closest('#login-form') && event.detail.xhr.status === 200) {
            // Login successful - hide overlay
            this.hideWithSuccess();
        }
    }

    hideWithSuccess() {
        // Show success state briefly before hiding
        const button = this.form.querySelector('.login-button');
        const buttonText = button.querySelector('.button-text');
        const spinner = button.querySelector('.loading-spinner');
        
        buttonText.textContent = '✓ Success!';
        buttonText.style.opacity = '1';
        spinner.style.display = 'none';
        button.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
        
        setTimeout(() => {
            this.hide();
            // Redirect or reload page after animation
            setTimeout(() => {
                window.location.href = '/';
            }, 500);
        }, 1000);
    }

    showErrorMessage(message) {
        // Remove existing error message
        const existingError = this.overlay.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }
        
        // Create error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.cssText = `
            color: #dc2626;
            background: #fee2e2;
            padding: 12px 16px;
            border-radius: 8px;
            margin-top: 15px;
            font-size: 14px;
            border: 1px solid #fecaca;
            animation: slideDown 0.3s ease-out;
        `;
        errorDiv.textContent = message;
        
        // Insert after form
        const formContainer = this.overlay.querySelector('.login-form-container');
        formContainer.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.style.animation = 'slideUp 0.3s ease-out';
                setTimeout(() => errorDiv.remove(), 300);
            }
        }, 5000);
    }

    // Public methods for external control
    toggle() {
        if (this.isVisible()) {
            this.hide();
        } else {
            this.show();
        }
    }

    // Method to trigger overlay from external code
    static show() {
        if (window.loginOverlay) {
            window.loginOverlay.show();
        }
    }

    static hide() {
        if (window.loginOverlay) {
            window.loginOverlay.hide();
        }
    }
}

// Initialize overlay when script loads
window.loginOverlay = new LoginOverlay();

// Add animation keyframes to document
const style = document.createElement('style');
style.textContent = `
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideUp {
        from { opacity: 1; transform: translateY(0); }
        to { opacity: 0; transform: translateY(-10px); }
    }
`;
document.head.appendChild(style);