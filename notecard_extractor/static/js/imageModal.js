/**
 * Unified Image Modal Library
 * Provides reusable functionality for image modals: zoom, pan, rotation, unneeded checkbox
 */

class ImageModal {
    constructor(config) {
        this.config = {
            container: config.container,
            imageElement: config.imageElement,
            checkboxId: config.checkboxId,
            checkboxLabelSelector: config.checkboxLabelSelector,
            rotationDisplayId: config.rotationDisplayId,
            rotateCCWId: config.rotateCCWId,
            rotateCWId: config.rotateCWId,
            onRotationChange: config.onRotationChange || (() => {}),
            onUnneededChange: config.onUnneededChange || (() => {}),
            getCurrentRotation: config.getCurrentRotation || (() => 0),
            getCurrentUnneeded: config.getCurrentUnneeded || (() => false),
            canRotate: config.canRotate !== false,
            canToggleUnneeded: config.canToggleUnneeded !== false,
            enableZoom: config.enableZoom !== false,
            enablePan: config.enablePan !== false,
        };

        this.zoomed = false;
        this.transform = { x: 0, y: 0, scale: 1 };
        this.isDragging = false;
        this.dragStartX = 0;
        this.dragStartY = 0;
        this.dragStartPosX = 0;
        this.dragStartPosY = 0;
        this.hasDragged = false;

        this.init();
    }

    init() {
        this.container = document.querySelector(this.config.container);
        this.image = document.querySelector(this.config.imageElement);
        
        if (!this.container || !this.image) {
            console.warn('ImageModal: Container or image element not found');
            return;
        }

        // Initialize checkbox handlers
        if (this.config.canToggleUnneeded) {
            this.initUnneededCheckbox();
        }

        // Initialize rotation handlers
        if (this.config.canRotate) {
            this.initRotationControls();
        }

        // Initialize zoom/pan handlers
        if (this.config.enableZoom || this.config.enablePan) {
            this.initZoomPan();
        }
    }

    initUnneededCheckbox() {
        const checkbox = document.getElementById(this.config.checkboxId);
        if (!checkbox) {
            // Checkbox doesn't exist yet, will be initialized when shown
            console.log('ImageModal: Checkbox not found:', this.config.checkboxId);
            return false;
        }
        
        console.log('ImageModal: Initializing checkbox handlers for:', this.config.checkboxId);

        const label = this.config.checkboxLabelSelector 
            ? document.querySelector(this.config.checkboxLabelSelector)
            : null;
        
        const wrapper = checkbox.closest('.unneeded-checkbox-wrapper') || 
                       checkbox.closest('.edit-modal-unneeded-checkbox-wrapper');

        // Use capture phase to ensure these handlers run before drag handlers
        const handleCheckboxInteraction = (e) => {
            e.stopPropagation();
            e.stopImmediatePropagation();
        };

        // Create a single handler function that will be reused
        const handleCheckboxChange = (e) => {
            handleCheckboxInteraction(e);
            // Get fresh reference to checkbox in case it was recreated
            const currentCheckbox = document.getElementById(this.config.checkboxId);
            if (!currentCheckbox) {
                console.error('ImageModal: Checkbox not found after event');
                return;
            }
            const isChecked = currentCheckbox.checked;
            console.log('ImageModal: Checkbox state changed to:', isChecked);
            if (this.config.onUnneededChange) {
                console.log('ImageModal: Calling onUnneededChange callback');
                try {
                    this.config.onUnneededChange(isChecked);
                } catch (error) {
                    console.error('ImageModal: Error in onUnneededChange callback:', error);
                }
            } else {
                console.warn('ImageModal: onUnneededChange callback not defined');
            }
        };

        // Use event delegation on the container to handle all checkbox interactions
        // This is more reliable than cloning and ensures handlers are always attached
        if (this.container) {
            // Remove any existing handler to avoid duplicates
            if (this._containerCheckboxHandler) {
                this.container.removeEventListener('click', this._containerCheckboxHandler, true);
                this.container.removeEventListener('change', this._containerCheckboxHandler, true);
            }
            
            // Create a handler for wrapper/label clicks only (checkbox clicks are handled directly)
            // Query elements dynamically inside the handler to avoid stale closures
            this._containerCheckboxHandler = (e) => {
                const target = e.target;
                const checkbox = document.getElementById(this.config.checkboxId);
                
                // Check if the event is related to our checkbox
                if (!checkbox) return;
                
                // Query label and wrapper dynamically to avoid stale references
                const currentLabel = this.config.checkboxLabelSelector 
                    ? document.querySelector(this.config.checkboxLabelSelector)
                    : null;
                const currentWrapper = checkbox.closest('.unneeded-checkbox-wrapper') || 
                                     checkbox.closest('.edit-modal-unneeded-checkbox-wrapper');
                
                // Only handle wrapper or label clicks, not direct checkbox clicks
                const isCheckbox = target === checkbox || target.id === this.config.checkboxId;
                const isLabel = currentLabel && (target === currentLabel || target.matches(this.config.checkboxLabelSelector));
                const isWrapper = currentWrapper && (target === currentWrapper || target.closest('.unneeded-checkbox-wrapper') === currentWrapper || target.closest('.edit-modal-unneeded-checkbox-wrapper') === currentWrapper);
                
                // Skip if clicking directly on checkbox (handled by direct handlers)
                if (isCheckbox) return;
                
                // Only handle wrapper or label clicks
                if (isLabel || isWrapper) {
                    console.log('ImageModal: Container event delegation handler fired', { isCheckbox, isLabel, isWrapper, target: target.tagName, targetId: target.id });
                    handleCheckboxInteraction(e);
                    
                    // Toggle checkbox when clicking wrapper or label
                    if ((isWrapper && target === currentWrapper) || (isLabel && target === currentLabel)) {
                        checkbox.checked = !checkbox.checked;
                        // Trigger change event manually
                        const changeEvent = new Event('change', { bubbles: true, cancelable: true });
                        checkbox.dispatchEvent(changeEvent);
                    }
                }
            };
            
            // Attach to container with capture phase
            this.container.addEventListener('click', this._containerCheckboxHandler, true);
            this.container.addEventListener('change', this._containerCheckboxHandler, true);
        }
        
        // Also attach directly to checkbox for immediate response
        // Note: We use stopImmediatePropagation to prevent container delegation from also handling
        checkbox.addEventListener('mousedown', handleCheckboxInteraction, true);
        checkbox.addEventListener('click', (e) => {
            // Only prevent propagation, don't call handleCheckboxChange here
            // The change event will fire automatically and handle the state change
            e.stopImmediatePropagation();
        }, true);
        checkbox.addEventListener('change', (e) => {
            console.log('ImageModal: Direct checkbox change handler fired');
            e.stopImmediatePropagation(); // Prevent container handler from also firing
            handleCheckboxChange(e);
        }, true);

        // Handle label clicks directly
        if (label) {
            label.addEventListener('mousedown', handleCheckboxInteraction, true);
            label.addEventListener('click', (e) => {
                handleCheckboxInteraction(e);
                checkbox.checked = !checkbox.checked;
                // Trigger change event manually
                const changeEvent = new Event('change', { bubbles: true, cancelable: true });
                checkbox.dispatchEvent(changeEvent);
            }, true);
        }
        
        // Handle wrapper clicks directly
        if (wrapper) {
            wrapper.addEventListener('click', (e) => {
                // Only handle if clicking directly on wrapper div itself
                if (e.target === wrapper) {
                    handleCheckboxInteraction(e);
                    checkbox.checked = !checkbox.checked;
                    // Trigger change event manually
                    const changeEvent = new Event('change', { bubbles: true, cancelable: true });
                    checkbox.dispatchEvent(changeEvent);
                }
            }, true);
        }
        
        console.log('ImageModal: Checkbox handlers attached successfully');
        return true;
    }
    
    ensureInitialized() {
        // Re-query container and image in case they weren't available during init
        this.container = document.querySelector(this.config.container);
        this.image = document.querySelector(this.config.imageElement);
        
        if (!this.container) {
            console.warn('ImageModal: Container not found during ensureInitialized:', this.config.container);
        }
        if (!this.image) {
            console.warn('ImageModal: Image element not found during ensureInitialized:', this.config.imageElement);
        }
        
        // Re-initialize handlers if elements exist now but weren't before
        if (this.config.canToggleUnneeded) {
            console.log('ImageModal: ensureInitialized called, re-initializing checkbox');
            this.initUnneededCheckbox();
        }
        
        // Also re-initialize rotation controls if needed
        if (this.config.canRotate) {
            this.initRotationControls();
        }
    }

    initRotationControls() {
        const rotateCCW = document.getElementById(this.config.rotateCCWId);
        const rotateCW = document.getElementById(this.config.rotateCWId);

        if (rotateCCW) {
            rotateCCW.addEventListener('click', (e) => {
                e.stopPropagation();
                e.stopImmediatePropagation();
                const newRotation = (this.config.getCurrentRotation() - 90 + 360) % 360;
                this.config.onRotationChange(newRotation);
            });
        }

        if (rotateCW) {
            rotateCW.addEventListener('click', (e) => {
                e.stopPropagation();
                e.stopImmediatePropagation();
                const newRotation = (this.config.getCurrentRotation() + 90) % 360;
                this.config.onRotationChange(newRotation);
            });
        }
    }

    initZoomPan() {
        // Check if clicking on interactive elements
        const isInteractiveElement = (target) => {
            return target.closest('.rotation-controls') ||
                   target.closest('.rotation-button') ||
                   target.closest('.rotation-display') ||
                   target.closest('.unneeded-checkbox-wrapper') ||
                   target.closest('.unneeded-checkbox') ||
                   target.closest('.unneeded-checkbox-label') ||
                   target.closest('.image-nav-arrow') ||
                   target.closest('.image-overlay-close') ||
                   target.closest('.edit-modal-close') ||
                   target.closest('.edit-modal-image-nav') ||
                   target.closest('.edit-modal-image-controls') ||
                   target.id === this.config.checkboxId ||
                   (this.config.checkboxLabelSelector && target.matches(this.config.checkboxLabelSelector));
        };

        this.container.addEventListener('mousedown', (e) => {
            // Don't handle if clicking on interactive elements
            if (isInteractiveElement(e.target)) {
                return;
            }

            if (this.zoomed && this.config.enablePan) {
                // Start drag
                this.isDragging = true;
                this.hasDragged = false;
                this.dragStartX = e.clientX;
                this.dragStartY = e.clientY;
                this.dragStartPosX = this.transform.x;
                this.dragStartPosY = this.transform.y;
                e.preventDefault();
            } else if (this.config.enableZoom) {
                // Track for potential drag
                this.isDragging = true;
                this.hasDragged = false;
                this.dragStartX = e.clientX;
                this.dragStartY = e.clientY;
            }
        });

        document.addEventListener('mousemove', (e) => {
            if (!this.isDragging) return;

            const deltaX = Math.abs(e.clientX - this.dragStartX);
            const deltaY = Math.abs(e.clientY - this.dragStartY);

            // If moved more than 5 pixels, consider it a drag
            if (deltaX > 5 || deltaY > 5) {
                this.hasDragged = true;
            }

            if (this.zoomed && this.hasDragged && this.config.enablePan) {
                // Update pan position
                this.transform.x = this.dragStartPosX + (e.clientX - this.dragStartX);
                this.transform.y = this.dragStartPosY + (e.clientY - this.dragStartY);
                this.updateTransform();
            }
        });

        this.container.addEventListener('mouseup', (e) => {
            // First check if clicking on interactive elements
            if (isInteractiveElement(e.target)) {
                this.isDragging = false;
                this.hasDragged = false;
                return;
            }

            if (!this.isDragging) return;

            // If it was a drag, don't toggle zoom
            if (this.hasDragged) {
                this.isDragging = false;
                this.hasDragged = false;
                return;
            }

            // If it was just a click (no drag), toggle zoom
            if (this.config.enableZoom) {
                this.toggleZoom();
            }

            this.isDragging = false;
            this.hasDragged = false;
        });
    }

    toggleZoom() {
        this.zoomed = !this.zoomed;
        if (!this.zoomed) {
            this.transform = { x: 0, y: 0, scale: 1 };
        } else {
            this.transform.scale = 2;
        }
        this.updateTransform();
    }

    updateTransform() {
        if (!this.image) return;

        const rotation = this.config.getCurrentRotation ? this.config.getCurrentRotation() : 0;
        
        if (this.zoomed) {
            this.image.style.transform = `translate(${this.transform.x}px, ${this.transform.y}px) scale(${this.transform.scale}) rotate(${rotation}deg)`;
            this.image.classList.add('zoomed');
            this.container.classList.add('zoomed');
        } else {
            this.image.style.transform = `rotate(${rotation}deg)`;
            this.image.classList.remove('zoomed');
            this.container.classList.remove('zoomed');
        }
        this.image.style.transformOrigin = 'center center';
    }

    reset() {
        this.zoomed = false;
        this.transform = { x: 0, y: 0, scale: 1 };
        this.updateTransform();
    }

    updateRotationDisplay() {
        if (this.config.rotationDisplayId) {
            const display = document.getElementById(this.config.rotationDisplayId);
            if (display) {
                display.textContent = `${this.config.getCurrentRotation()}°`;
            }
        }
    }

    updateUnneededCheckbox() {
        if (!this.config.canToggleUnneeded) return;
        
        const checkbox = document.getElementById(this.config.checkboxId);
        if (checkbox) {
            checkbox.checked = this.config.getCurrentUnneeded();
            // Enable/disable based on whether unneeded can be toggled for current image
            // This is handled by the caller's getCurrentUnneeded function context
            if (this.config.shouldDisableCheckbox) {
                checkbox.disabled = this.config.shouldDisableCheckbox();
            }
        }
    }

    updateImageUnneededStyle() {
        if (!this.image) return;
        
        if (this.config.getCurrentUnneeded()) {
            this.image.classList.add('image-unneeded');
        } else {
            this.image.classList.remove('image-unneeded');
        }
    }
}
