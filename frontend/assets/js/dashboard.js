/**
 * ZionX ERP - Dashboard Module
 * Gestión de gráficos y visualizaciones del dashboard
 * @version 3.0.0
 */

(function() {
    'use strict';

    const DashboardModule = {
        // Configuración de colores consistente
        colors: {
            primary: 'rgb(13, 110, 253)',
            success: 'rgb(25, 135, 84)',
            danger: 'rgb(220, 53, 69)',
            warning: 'rgb(255, 193, 7)',
            info: 'rgb(13, 202, 240)',
            secondary: 'rgb(108, 117, 125)',
            
            // Versiones con transparencia
            primaryAlpha: 'rgba(13, 110, 253, 0.1)',
            successAlpha: 'rgba(25, 135, 84, 0.1)',
            dangerAlpha: 'rgba(220, 53, 69, 0.1)',
            warningAlpha: 'rgba(255, 193, 7, 0.1)',
            infoAlpha: 'rgba(13, 202, 240, 0.1)',
        },

        // Configuración global de Chart.js
        chartDefaults: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 800,
                easing: 'easeInOutQuart'
            },
            interaction: {
                mode: 'index',
                intersect: false,
            }
        },

        init() {
            if (!this.checkDependencies()) return;
            
            this.animateMetricCards();
            this.initCharts();
            this.setupInteractions();
            this.startAutoRefresh();
            
            console.log('✅ Dashboard Module inicializado');
        },

        checkDependencies() {
            if (typeof Chart === 'undefined') {
                console.error('❌ Chart.js no está cargado');
                return false;
            }
            return true;
        },

        animateMetricCards() {
            const cards = document.querySelectorAll('.metric-card');
            cards.forEach((card, index) => {
                card.style.animation = `cardEnter 0.5s ease ${index * 0.1}s both`;
                
                // Efecto de conteo animado para números
                const numberElement = card.querySelector('.metric-value');
                if (numberElement) {
                    this.animateNumber(numberElement);
                }
            });
        },

        animateNumber(element) {
            const finalValue = parseFloat(element.textContent.replace(/[^0-9.-]/g, ''));
            if (isNaN(finalValue)) return;

            const duration = 1000;
            const steps = 30;
            const increment = finalValue / steps;
            const delay = duration / steps;
            let current = 0;
            const prefix = element.textContent.match(/^\$/)?.[0] || '';

            const timer = setInterval(() => {
                current += increment;
                if (current >= finalValue) {
                    element.textContent = prefix + finalValue.toFixed(2);
                    clearInterval(timer);
                } else {
                    element.textContent = prefix + current.toFixed(2);
                }
            }, delay);
        },

        initCharts() {
            this.initSalesChart();
            this.initTopProductsChart();
        },

        initSalesChart() {
            const container = document.querySelector('[data-chart-labels]');
            if (!container) return;

            const ctx = document.getElementById('ventasComprasChart');
            if (!ctx) return;

            try {
                const labels = JSON.parse(container.dataset.chartLabels);
                const ventasData = JSON.parse(container.dataset.chartVentas);
                const comprasData = JSON.parse(container.dataset.chartCompras);

                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Ventas',
                            data: ventasData,
                            borderColor: this.colors.success,
                            backgroundColor: this.colors.successAlpha,
                            tension: 0.4,
                            fill: true,
                            borderWidth: 3,
                            pointRadius: 5,
                            pointHoverRadius: 7,
                            pointBackgroundColor: this.colors.success,
                            pointBorderColor: '#fff',
                            pointBorderWidth: 2
                        }, {
                            label: 'Compras',
                            data: comprasData,
                            borderColor: this.colors.primary,
                            backgroundColor: this.colors.primaryAlpha,
                            tension: 0.4,
                            fill: true,
                            borderWidth: 3,
                            pointRadius: 5,
                            pointHoverRadius: 7,
                            pointBackgroundColor: this.colors.primary,
                            pointBorderColor: '#fff',
                            pointBorderWidth: 2
                        }]
                    },
                    options: {
                        ...this.chartDefaults,
                        plugins: {
                            legend: {
                                display: true,
                                position: 'top',
                                labels: {
                                    usePointStyle: true,
                                    padding: 20,
                                    font: {
                                        size: 13,
                                        weight: '500'
                                    }
                                }
                            },
                            tooltip: {
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                titleColor: '#fff',
                                bodyColor: '#fff',
                                borderColor: 'rgba(255, 255, 255, 0.2)',
                                borderWidth: 1,
                                padding: 12,
                                displayColors: true,
                                callbacks: {
                                    label: (context) => {
                                        return `${context.dataset.label}: $${context.parsed.y.toFixed(2)}`;
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                grid: {
                                    color: 'rgba(0, 0, 0, 0.05)',
                                    drawBorder: false
                                },
                                ticks: {
                                    callback: (value) => '$' + value.toFixed(0),
                                    font: {
                                        size: 12
                                    }
                                }
                            },
                            x: {
                                grid: {
                                    display: false
                                },
                                ticks: {
                                    font: {
                                        size: 12
                                    }
                                }
                            }
                        }
                    }
                });

                console.log('✅ Gráfico de Ventas vs Compras creado');
            } catch (error) {
                console.error('Error creando gráfico de ventas:', error);
            }
        },

        initTopProductsChart() {
            const container = document.querySelector('[data-chart-labels]');
            if (!container) return;

            const ctx = document.getElementById('topProductosChart');
            if (!ctx) return;

            try {
                const labels = JSON.parse(container.dataset.chartTopLabels);
                const data = JSON.parse(container.dataset.chartTopData);

                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: labels,
                        datasets: [{
                            data: data,
                            backgroundColor: [
                                this.colors.success,
                                this.colors.primary,
                                this.colors.warning,
                                this.colors.danger,
                                this.colors.secondary
                            ],
                            borderColor: '#fff',
                            borderWidth: 3,
                            hoverBorderWidth: 4,
                            hoverOffset: 15
                        }]
                    },
                    options: {
                        ...this.chartDefaults,
                        cutout: '65%',
                        plugins: {
                            legend: {
                                display: true,
                                position: 'bottom',
                                labels: {
                                    usePointStyle: true,
                                    padding: 15,
                                    font: {
                                        size: 11,
                                        weight: '500'
                                    },
                                    generateLabels: (chart) => {
                                        const data = chart.data;
                                        if (data.labels.length && data.datasets.length) {
                                            return data.labels.map((label, i) => {
                                                const value = data.datasets[0].data[i];
                                                return {
                                                    text: `${label}: ${value} un.`,
                                                    fillStyle: data.datasets[0].backgroundColor[i],
                                                    hidden: false,
                                                    index: i
                                                };
                                            });
                                        }
                                        return [];
                                    }
                                }
                            },
                            tooltip: {
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                padding: 12,
                                callbacks: {
                                    label: (context) => {
                                        const label = context.label || '';
                                        const value = context.parsed;
                                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                        const percentage = ((value / total) * 100).toFixed(1);
                                        return `${label}: ${value} unidades (${percentage}%)`;
                                    }
                                }
                            }
                        }
                    }
                });

                console.log('✅ Gráfico de Top Productos creado');
            } catch (error) {
                console.error('Error creando gráfico de productos:', error);
            }
        },

        setupInteractions() {
            // Efecto hover para tarjetas métricas
            document.querySelectorAll('.metric-card').forEach(card => {
                card.addEventListener('mouseenter', () => {
                    card.style.transform = 'translateY(-8px) scale(1.02)';
                });
                
                card.addEventListener('mouseleave', () => {
                    card.style.transform = 'translateY(0) scale(1)';
                });
            });

            // Animación para tabla de stock bajo
            const stockTable = document.querySelector('.table-responsive table');
            if (stockTable) {
                const rows = stockTable.querySelectorAll('tbody tr');
                rows.forEach((row, index) => {
                    row.style.animation = `fadeInUp 0.4s ease ${index * 0.05}s both`;
                });
            }
        },

        startAutoRefresh() {
            // Opcional: Auto-refresh cada 5 minutos
            // setInterval(() => {
            //     window.location.reload();
            // }, 5 * 60 * 1000);
        }
    };

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => DashboardModule.init());
    } else {
        DashboardModule.init();
    }

    // Exponer módulo globalmente
    window.DashboardModule = DashboardModule;

})();
