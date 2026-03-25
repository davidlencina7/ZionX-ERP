/**
 * ZionX ERP - Core Application JavaScript
 * Funcionalidades centralizadas y modulares
 * @version 3.0.0
 */

(function() {
    'use strict';

    // ========================================
    // 🎨 THEME MANAGEMENT
    // ========================================
    const ThemeManager = {
        init() {
            this.applyStoredTheme();
            this.setupThemeToggle();
            this.applyTransitions();
        },

        applyStoredTheme() {
            // Aplicar tema desde localStorage al cargar la página
            try {
                const storedTheme = localStorage.getItem('piupiu_tema');
                if (storedTheme && (storedTheme === 'light' || storedTheme === 'dark')) {
                    const currentTheme = document.documentElement.getAttribute('data-theme');
                    if (currentTheme !== storedTheme) {
                        document.documentElement.setAttribute('data-theme', storedTheme);
                        this.updateThemeIcon(storedTheme);
                    }
                }
            } catch (e) {
                console.warn('No se pudo leer tema de localStorage:', e);
            }
        },

        setupThemeToggle() {
            // Buscar botón por múltiples IDs posibles
            const themeToggle = document.getElementById('theme-toggle') || 
                               document.getElementById('btn-toggle-tema');
            
            if (!themeToggle) {
                console.warn('Botón de cambio de tema no encontrado');
                return;
            }

            themeToggle.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleTheme();
            });
        },

        toggleTheme() {
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            console.log('Cambiando tema de', currentTheme, 'a', newTheme);
            
            // Aplicar tema inmediatamente con animación suave
            html.style.transition = 'background-color 0.3s ease, color 0.3s ease';
            html.setAttribute('data-theme', newTheme);
            
            // Guardar en localStorage
            try {
                localStorage.setItem('piupiu_tema', newTheme);
                console.log('Tema guardado en localStorage:', newTheme);
            } catch (e) {
                console.warn('No se pudo guardar tema en localStorage:', e);
            }
            
            // Actualizar icono del botón inmediatamente
            this.updateThemeIcon(newTheme);
            
            // Actualizar input hidden del formulario si existe
            const inputTema = document.getElementById('input-tema');
            if (inputTema) {
                inputTema.value = newTheme;
            }
            
            // Guardar preferencia en servidor (no bloqueante)
            fetch('/auth/cambiar-tema', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ tema: newTheme })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('✅ Tema guardado en servidor correctamente');
                } else {
                    console.warn('⚠️ Error al guardar tema en servidor:', data.message);
                }
            })
            .catch(err => {
                console.error('❌ Error al guardar tema:', err);
                // Intentar con form data como fallback
                return fetch('/auth/cambiar-tema', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `tema=${newTheme}&csrf_token=${this.getCSRFToken()}`
                });
            });
        },

        updateThemeIcon(theme) {
            const icon = document.querySelector('#theme-toggle i, #btn-toggle-tema i, #icono-tema');
            if (!icon) return;

            icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
            
            const button = icon.closest('button');
            if (button) {
                button.setAttribute('title', theme === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro');
            }
        },

        applyTransitions() {
            document.documentElement.style.transition = 'background-color 0.3s ease, color 0.3s ease';
        },

        getCSRFToken() {
            const token = document.querySelector('meta[name="csrf-token"]');
            return token ? token.getAttribute('content') : '';
        }
    };

    // ========================================
    // 🔔 TOAST NOTIFICATIONS
    // ========================================
    const ToastManager = {
        container: null,

        init() {
            this.createContainer();
            this.processFlashMessages();
        },

        createContainer() {
            if (document.getElementById('toast-container')) return;

            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'position-fixed top-0 end-0 p-3';
            this.container.style.zIndex = '9999';
            document.body.appendChild(this.container);
        },

        processFlashMessages() {
            const alerts = document.querySelectorAll('.alert:not(.toast-processed)');
            alerts.forEach((alert, index) => {
                const category = this.getAlertCategory(alert);
                const message = alert.textContent.trim();
                
                // Ocultar alert original
                alert.style.display = 'none';
                alert.classList.add('toast-processed');
                
                // Mostrar como toast con delay escalonado
                setTimeout(() => {
                    this.show(message, category);
                }, index * 150);
            });
        },

        getAlertCategory(alert) {
            if (alert.classList.contains('alert-success')) return 'success';
            if (alert.classList.contains('alert-danger')) return 'danger';
            if (alert.classList.contains('alert-warning')) return 'warning';
            if (alert.classList.contains('alert-info')) return 'info';
            return 'info';
        },

        show(message, type = 'info', duration = 4000) {
            const toast = this.createToast(message, type);
            this.container.appendChild(toast);

            // Animación de entrada
            setTimeout(() => toast.classList.add('show'), 10);

            // Auto-close
            setTimeout(() => this.hide(toast), duration);
        },

        createToast(message, type) {
            const icons = {
                success: 'bi-check-circle-fill',
                danger: 'bi-exclamation-circle-fill',
                warning: 'bi-exclamation-triangle-fill',
                info: 'bi-info-circle-fill'
            };

            const colors = {
                success: 'text-bg-success',
                danger: 'text-bg-danger',
                warning: 'text-bg-warning',
                info: 'text-bg-info'
            };

            const toast = document.createElement('div');
            toast.className = `toast align-items-center ${colors[type]} border-0`;
            toast.setAttribute('role', 'alert');
            toast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="bi ${icons[type]} me-2"></i>
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            `;

            // Close button
            toast.querySelector('.btn-close').addEventListener('click', () => this.hide(toast));

            return toast;
        },

        hide(toast) {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }
    };

    // ========================================
    // ⚡ LOADING STATES
    // ========================================
    const LoadingManager = {
        init() {
            this.setupFormSubmitLoading();
            this.setupButtonLoading();
        },

        setupFormSubmitLoading() {
            document.querySelectorAll('form').forEach(form => {
                form.addEventListener('submit', (e) => {
                    const submitBtn = form.querySelector('button[type="submit"]');
                    if (submitBtn && !submitBtn.disabled) {
                        this.showButtonLoading(submitBtn);
                    }
                });
            });
        },

        setupButtonLoading() {
            document.querySelectorAll('[data-loading]').forEach(btn => {
                btn.addEventListener('click', () => {
                    this.showButtonLoading(btn);
                });
            });
        },

        showButtonLoading(button) {
            const originalHTML = button.innerHTML;
            button.setAttribute('data-original-html', originalHTML);
            button.disabled = true;
            button.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                Procesando...
            `;
        },

        hideButtonLoading(button) {
            const originalHTML = button.getAttribute('data-original-html');
            if (originalHTML) {
                button.innerHTML = originalHTML;
                button.disabled = false;
                button.removeAttribute('data-original-html');
            }
        }
    };

    // ========================================
    // 🎯 NAVIGATION ANIMATIONS
    // ========================================
    const NavigationManager = {
        init() {
            this.setupSmoothNavigation();
            this.highlightActiveMenu();
        },

        setupSmoothNavigation() {
            document.querySelectorAll('.nav-link').forEach(link => {
                link.addEventListener('click', (e) => {
                    // Agregar clase de animación
                    link.classList.add('nav-link-clicked');
                    setTimeout(() => link.classList.remove('nav-link-clicked'), 300);
                });
            });
        },

        highlightActiveMenu() {
            const currentPath = window.location.pathname;
            document.querySelectorAll('.nav-link').forEach(link => {
                const href = link.getAttribute('href');
                if (href && currentPath.includes(href) && href !== '/') {
                    link.classList.add('active');
                }
            });
        }
    };

    // ========================================
    // 📊 TABLE ENHANCEMENTS
    // ========================================
    const TableManager = {
        init() {
            this.setupSortable();
            this.setupSearch();
            this.animateRows();
        },

        setupSortable() {
            document.querySelectorAll('table thead th[data-sortable]').forEach(th => {
                th.style.cursor = 'pointer';
                th.addEventListener('click', () => this.sortTable(th));
            });
        },

        sortTable(th) {
            // Implementación básica de ordenamiento
            console.log('Sorting by:', th.textContent);
            // TODO: Implementar lógica de ordenamiento
        },

        setupSearch() {
            const searchInputs = document.querySelectorAll('[data-table-search]');
            searchInputs.forEach(input => {
                const tableId = input.getAttribute('data-table-search');
                const table = document.getElementById(tableId);
                
                if (table) {
                    input.addEventListener('keyup', (e) => {
                        this.filterTable(table, e.target.value);
                    });
                }
            });
        },

        filterTable(table, searchTerm) {
            const rows = table.querySelectorAll('tbody tr');
            const term = searchTerm.toLowerCase();

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(term) ? '' : 'none';
            });
        },

        animateRows() {
            const tables = document.querySelectorAll('table tbody');
            tables.forEach(tbody => {
                const rows = tbody.querySelectorAll('tr');
                rows.forEach((row, index) => {
                    row.style.animation = `fadeInUp 0.3s ease ${index * 0.03}s both`;
                });
            });
        }
    };

    // ========================================
    // 🔢 NUMBER FORMATTING
    // ========================================
    const NumberFormatter = {
        init() {
            this.formatCurrency();
            this.formatNumbers();
        },

        formatCurrency() {
            document.querySelectorAll('[data-currency]').forEach(el => {
                const value = parseFloat(el.textContent);
                if (!isNaN(value)) {
                    el.textContent = this.toCurrency(value);
                }
            });
        },

        formatNumbers() {
            document.querySelectorAll('[data-number]').forEach(el => {
                const value = parseFloat(el.textContent);
                if (!isNaN(value)) {
                    el.textContent = this.toNumber(value);
                }
            });
        },

        toCurrency(value) {
            return new Intl.NumberFormat('es-AR', {
                style: 'currency',
                currency: 'ARS'
            }).format(value);
        },

        toNumber(value) {
            return new Intl.NumberFormat('es-AR').format(value);
        }
    };

    // ========================================
    // 🚀 INITIALIZATION
    // ========================================
    function initApp() {
        // Esperar a que el DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initializeModules);
        } else {
            initializeModules();
        }
    }

    function initializeModules() {
        console.log('🚀 ZionX ERP - Inicializando...');

        // Inicializar módulos
        ThemeManager.init();
        ToastManager.init();
        LoadingManager.init();
        NavigationManager.init();
        TableManager.init();
        NumberFormatter.init();

        // Marcar como inicializado
        document.body.classList.add('piupiu-initialized');
        
        console.log('✅ ZionX ERP - Módulos cargados exitosamente');
    }

    // Iniciar aplicación
    initApp();

    // Exponer API pública
    window.PIUPIU = {
        toast: (message, type, duration) => ToastManager.show(message, type, duration),
        showLoading: (button) => LoadingManager.showButtonLoading(button),
        hideLoading: (button) => LoadingManager.hideButtonLoading(button),
        version: '3.0.0'
    };

})();
