// Main JavaScript for Crop Recommendation System
// Enhanced UI/UX interactions


(function() {
    'use strict';

    // Initialize on DOM ready
    document.addEventListener('DOMContentLoaded', function() {
        initAnimations();
        initFormEnhancements();
        initProgressBars();
        initTooltips();
        initSmoothScrolling();
        initLoadingStates();
    });

    // Animate elements on scroll
    function initAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver(function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);

        // Observe cards and stat cards
        document.querySelectorAll('.dashboard-card, .stat-card, .recommendation-card').forEach(card => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(card);
        });
    }

    // Enhance form interactions
    function initFormEnhancements() {
        // Add floating label effect
        const formControls = document.querySelectorAll('.form-control, .form-select');
        formControls.forEach(control => {
            // Check if field has value on load
            if (control.value) {
                control.classList.add('has-value');
            }

            // Add class on focus
            control.addEventListener('focus', function() {
                this.classList.add('focused');
            });

            // Remove class on blur
            control.addEventListener('blur', function() {
                this.classList.remove('focused');
                if (this.value) {
                    this.classList.add('has-value');
                } else {
                    this.classList.remove('has-value');
                }
            });

            // Real-time validation feedback
            control.addEventListener('input', function() {
                if (this.checkValidity()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                } else {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                }
            });
        });

        // Form submission loading state
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn && !form.dataset.noLoading) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
                }
            });
        });
    }

    // Animate progress bars on scroll
    function initProgressBars() {
        const progressBars = document.querySelectorAll('.progress-bar');
        
        const progressObserver = new IntersectionObserver(function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const bar = entry.target;
                    const width = bar.getAttribute('aria-valuenow') || bar.style.width;
                    bar.style.width = '0%';
                    setTimeout(() => {
                        bar.style.width = width + '%';
                    }, 100);
                    progressObserver.unobserve(bar);
                }
            });
        }, { threshold: 0.5 });

        progressBars.forEach(bar => {
            progressObserver.observe(bar);
        });
    }

    // Initialize Bootstrap tooltips
    function initTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Smooth scrolling for anchor links
    function initSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                if (href !== '#' && href.length > 1) {
                    const target = document.querySelector(href);
                    if (target) {
                        e.preventDefault();
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                }
            });
        });
    }

    // Loading states for async operations
    function initLoadingStates() {
        // Show loading overlay for form submissions
        window.showLoading = function(message) {
            const overlay = document.createElement('div');
            overlay.className = 'loading-overlay';
            overlay.innerHTML = `
                <div class="text-center">
                    <div class="spinner-custom mb-3"></div>
                    <p class="text-muted">${message || 'Loading...'}</p>
                </div>
            `;
            document.body.appendChild(overlay);
            return overlay;
        };

        window.hideLoading = function(overlay) {
            if (overlay && overlay.parentNode) {
                overlay.parentNode.removeChild(overlay);
            }
        };
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Add ripple effect to buttons
    document.querySelectorAll('.btn').forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });

    // Add CSS for ripple effect
    const style = document.createElement('style');
    style.textContent = `
        .btn {
            position: relative;
            overflow: hidden;
        }
        .ripple {
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.6);
            transform: scale(0);
            animation: ripple-animation 0.6s ease-out;
            pointer-events: none;
        }
        @keyframes ripple-animation {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
        .form-control.focused,
        .form-select.focused {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 0.2rem rgba(25, 135, 84, 0.15);
        }
    `;
    document.head.appendChild(style);

    // Console log for debugging
    console.log('🚀 Crop Recommendation System - UI Enhanced');
})();

