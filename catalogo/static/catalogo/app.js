const PRODUCTS = typeof DJANGO_PRODUCTS !== 'undefined' ? DJANGO_PRODUCTS : [];

let state = {
    category: 'ALL',
    size: 'ALL',
    search: '',
    sort: 'featured',
    onlyFavs: false,
    favorites: new Set(),
    cart: JSON.parse(localStorage.getItem('dsclub-cart') || '[]'),
    activeModalProduct: null,
    selectedModalSize: null,
    selectedModalQty: 1
};

const gridEl = document.getElementById('product-grid');
const countEl = document.getElementById('product-count');
const titleEl = document.getElementById('collection-title');
const emptyEl = document.getElementById('empty-state');
const favBadgeEl = document.getElementById('fav-badge');
const cartBadgeEl = document.getElementById('cart-badge');

const themeToggleBtn = document.getElementById('theme-toggle-btn');
if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
        const isDark = document.documentElement.classList.toggle('dark');
        localStorage.setItem('dsclub-theme', isDark ? 'dark' : 'light');
        renderProducts();
    });
}

function formatPrice(value) {
    return 'S/ ' + Number(value).toFixed(2);
}

function getCostoEnvioActual() {
    return 0;
}

function saveCart() {
    localStorage.setItem('dsclub-cart', JSON.stringify(state.cart));
    updateCartBadge();
    renderCart();
}

function updateCartBadge() {
    if (!cartBadgeEl) return;
    const totalQty = state.cart.reduce((sum, item) => sum + item.qty, 0);
    cartBadgeEl.textContent = totalQty;
    cartBadgeEl.classList.toggle('hidden', totalQty === 0);
}

function updateFavBadge() {
    if (!favBadgeEl) return;
    const count = state.favorites.size;
    favBadgeEl.textContent = count;
    favBadgeEl.classList.toggle('hidden', count === 0);
}

function renderProducts() {
    if (!gridEl) return;
    const isDark = document.documentElement.classList.contains('dark');

    let filtered = PRODUCTS.filter(p => {
        const matchCat = state.category === 'ALL' || p.category === state.category;
        const matchSize = state.size === 'ALL' || (Array.isArray(p.sizes) && p.sizes.includes(state.size));
        const matchSearch = p.name.toLowerCase().includes(state.search.toLowerCase()) ||
                            p.category.toLowerCase().includes(state.search.toLowerCase());
        const matchFav = !state.onlyFavs || state.favorites.has(p.id);
        return matchCat && matchSize && matchSearch && matchFav;
    });

    if (state.sort === 'price-asc') {
        filtered.sort((a, b) => a.price - b.price);
    } else if (state.sort === 'price-desc') {
        filtered.sort((a, b) => b.price - a.price);
    }

    if (titleEl) {
        titleEl.textContent = state.onlyFavs
            ? 'MIS FAVORITOS'
            : (state.category === 'ALL' ? 'TODO EL STOCK' : state.category);
    }

    if (countEl) {
        countEl.textContent = `${filtered.length} ${filtered.length === 1 ? 'artículo' : 'artículos'}`;
    }

    if (filtered.length === 0) {
        gridEl.innerHTML = '';
        if (emptyEl) emptyEl.classList.remove('hidden');
        return;
    }

    if (emptyEl) emptyEl.classList.add('hidden');
    gridEl.innerHTML = filtered.map(product => {
        const isFav = state.favorites.has(product.id);
        const heartFill = isFav ? (isDark ? '#F5F5F5' : '#111111') : 'none';
        const oldPriceHtml = product.old_price
            ? `<span class="text-[11px] text-neutral-400 line-through">${formatPrice(product.old_price)}</span>`
            : '';

        return `
            <article class="group flex flex-col">
                <div class="relative bg-[#F3F3F3] dark:bg-[#171717] aspect-[4/5] w-full overflow-hidden transition-colors duration-300">
                    <span class="absolute top-3.5 left-3.5 z-10 bg-white/85 dark:bg-black/75 backdrop-blur-xs px-2 py-0.5 text-[11px] sm:text-xs font-bold tracking-tight uppercase text-black dark:text-white pointer-events-none">
                        ${product.tag}
                    </span>

                    <button onclick="toggleFavorite(${product.id}, event)" aria-label="Guardar en favoritos"
                        class="absolute top-3 right-3 z-10 p-1.5 rounded-full bg-white/75 dark:bg-black/60 text-black dark:text-white hover:scale-110 transition-transform cursor-pointer">
                        <svg class="w-[18px] h-[18px]" fill="${heartFill}" stroke="currentColor" stroke-width="1.7" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z"/>
                        </svg>
                    </button>

                    <img src="${product.image}" alt="${product.name}" loading="lazy"
                        onclick="openProductModal(${product.id})"
                        class="w-full h-full object-cover object-center group-hover:scale-[1.04] transition-transform duration-500 cursor-pointer">

                    <button onclick="openProductModal(${product.id})"
                        class="absolute inset-x-3 bottom-3 bg-white/95 dark:bg-[#141414]/95 hover:bg-black hover:text-white dark:hover:bg-white dark:hover:text-black text-black dark:text-white py-2 text-[11px] font-semibold uppercase tracking-widest opacity-0 translate-y-1 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-200 cursor-pointer shadow-sm">
                        + Agregar al carrito
                    </button>
                </div>

                <div class="pt-3 flex flex-col gap-1">
                    <div class="flex items-center justify-between text-[11px] text-neutral-400 dark:text-neutral-500 uppercase tracking-wider">
                        <span>${product.category}</span>
                        <span>${product.stock} disp.</span>
                    </div>
                    <h2 onclick="openProductModal(${product.id})" class="text-xs sm:text-[13px] font-medium text-neutral-900 dark:text-neutral-100 group-hover:underline cursor-pointer line-clamp-1">
                        ${product.name}
                    </h2>
                    <div class="flex items-baseline gap-2">
                        <p class="text-xs sm:text-[13px] font-semibold text-black dark:text-white">${formatPrice(product.price)}</p>
                        ${oldPriceHtml}
                    </div>
                </div>
            </article>
        `;
    }).join('');
}

window.toggleFavorite = function(id, event) {
    event.stopPropagation();
    if (state.favorites.has(id)) {
        state.favorites.delete(id);
    } else {
        state.favorites.add(id);
    }
    updateFavBadge();
    renderProducts();
};

window.openProductModal = function(id) {
    const product = PRODUCTS.find(p => p.id === id);
    if (!product) return;

    state.activeModalProduct = product;
    state.selectedModalSize = (Array.isArray(product.sizes) && product.sizes[0]) ? product.sizes[0] : 'ÚNICA';
    state.selectedModalQty = 1;

    document.getElementById('modal-img').src = product.image;
    document.getElementById('modal-img').alt = product.name;
    document.getElementById('modal-tag').textContent = `${product.tag} · ${product.category}`;
    document.getElementById('modal-name').textContent = product.name;
    document.getElementById('modal-price').textContent = formatPrice(product.price);

    const oldPriceEl = document.getElementById('modal-old-price');
    if (oldPriceEl) {
        if (product.old_price) {
            oldPriceEl.textContent = formatPrice(product.old_price);
            oldPriceEl.classList.remove('hidden');
        } else {
            oldPriceEl.classList.add('hidden');
        }
    }

    const descEl = document.getElementById('modal-desc');
    if (descEl) descEl.textContent = product.description || '';
    document.getElementById('modal-qty-val').textContent = '1';

    renderModalSizes();
    document.getElementById('product-modal').classList.remove('hidden');
};

function renderModalSizes() {
    const product = state.activeModalProduct;
    if (!product) return;
    const sizesContainer = document.getElementById('modal-sizes');
    if (!sizesContainer) return;

    const sizesList = Array.isArray(product.sizes) && product.sizes.length > 0 ? product.sizes : ['ÚNICA'];
    sizesContainer.innerHTML = sizesList.map(s => {
        const isSelected = s === state.selectedModalSize;
        const activeClasses = isSelected
            ? 'bg-black dark:bg-white text-white dark:text-black border-black dark:border-white'
            : 'border-neutral-300 dark:border-neutral-700 text-black dark:text-white hover:border-black dark:hover:border-white';
        return `
            <button type="button" onclick="selectModalSize('${s}')"
                class="border ${activeClasses} px-3.5 py-2 text-xs font-bold uppercase transition-colors cursor-pointer">
                ${s}
            </button>
        `;
    }).join('');
}

window.selectModalSize = function(size) {
    state.selectedModalSize = size;
    renderModalSizes();
};

const modalQtyMinus = document.getElementById('modal-qty-minus');
if (modalQtyMinus) {
    modalQtyMinus.addEventListener('click', () => {
        if (state.selectedModalQty > 1) {
            state.selectedModalQty -= 1;
            document.getElementById('modal-qty-val').textContent = state.selectedModalQty;
        }
    });
}

const modalQtyPlus = document.getElementById('modal-qty-plus');
if (modalQtyPlus) {
    modalQtyPlus.addEventListener('click', () => {
        const maxStock = state.activeModalProduct ? state.activeModalProduct.stock : 99;
        if (state.selectedModalQty < maxStock) {
            state.selectedModalQty += 1;
            document.getElementById('modal-qty-val').textContent = state.selectedModalQty;
        }
    });
}

const modalAddCartBtn = document.getElementById('modal-add-cart-btn');
if (modalAddCartBtn) {
    modalAddCartBtn.addEventListener('click', () => {
        const product = state.activeModalProduct;
        if (!product) return;

        const existing = state.cart.find(item => item.id === product.id && item.size === state.selectedModalSize);
        if (existing) {
            existing.qty = Math.min(product.stock, existing.qty + state.selectedModalQty);
        } else {
            state.cart.push({
                id: product.id,
                name: product.name,
                price: product.price,
                image: product.image,
                size: state.selectedModalSize,
                qty: state.selectedModalQty,
                maxStock: product.stock
            });
        }

        saveCart();
        document.getElementById('product-modal').classList.add('hidden');
        document.getElementById('cart-drawer').classList.remove('hidden');
    });
}

const closeModalBtn = document.getElementById('close-modal-btn');
if (closeModalBtn) {
    closeModalBtn.addEventListener('click', () => {
        document.getElementById('product-modal').classList.add('hidden');
    });
}

const productModalEl = document.getElementById('product-modal');
if (productModalEl) {
    productModalEl.addEventListener('click', (e) => {
        if (e.target.id === 'product-modal') {
            productModalEl.classList.add('hidden');
        }
    });
}

// =========================================================
// CARRITO LATERAL Y ENVÍO DE PEDIDO
// =========================================================
function renderCart() {
    const container = document.getElementById('cart-items-container');
    const checkoutBox = document.getElementById('checkout-form-box');
    const footerBox = document.getElementById('cart-footer');
    const subtitle = document.getElementById('cart-subtitle');
    const subtotalEl = document.getElementById('cart-subtotal');
    const shippingLabelEl = document.getElementById('cart-shipping-label');
    const shippingEl = document.getElementById('cart-shipping');
    const totalEl = document.getElementById('cart-total');

    const totalQty = state.cart.reduce((sum, i) => sum + i.qty, 0);
    if (subtitle) {
        subtitle.textContent = `${totalQty} ${totalQty === 1 ? 'prenda seleccionada' : 'prendas seleccionadas'}`;
    }

    if (state.cart.length === 0) {
        if (container) {
            container.innerHTML = `
                <div class="py-14 text-center">
                    <p class="text-xs font-bold uppercase tracking-wider text-neutral-500">Tu carrito está vacío</p>
                    <p class="text-[11px] text-neutral-400 mt-1">Selecciona cualquier prenda del catálogo para agregarla.</p>
                </div>
            `;
        }
        if (checkoutBox) checkoutBox.classList.add('hidden');
        if (footerBox) footerBox.classList.add('hidden');
        return;
    }

    if (checkoutBox) checkoutBox.classList.remove('hidden');
    if (footerBox) footerBox.classList.remove('hidden');

    let subtotalPrendas = 0;
    if (container) {
        container.innerHTML = state.cart.map((item, idx) => {
            const subtotal = item.price * item.qty;
            subtotalPrendas += subtotal;
            return `
                <div class="flex gap-3.5 pb-4 border-b border-neutral-100 dark:border-neutral-800">
                    <img src="${item.image}" alt="${item.name}" class="w-16 h-20 object-cover bg-neutral-100 dark:bg-neutral-800 shrink-0">
                    <div class="flex-1 min-w-0">
                        <div class="flex items-start justify-between gap-2">
                            <h3 class="text-xs font-bold uppercase truncate">${item.name}</h3>
                            <button onclick="removeCartItem(${idx})" class="text-[11px] text-neutral-400 hover:text-red-500 cursor-pointer">✕</button>
                        </div>
                        <p class="text-[11px] text-neutral-500 mt-0.5">Talla: <strong class="text-black dark:text-white">${item.size}</strong></p>
                        <div class="flex items-center justify-between mt-2">
                            <div class="inline-flex items-center border border-neutral-200 dark:border-neutral-700">
                                <button onclick="updateCartQty(${idx}, -1)" class="w-6 h-6 text-xs font-bold cursor-pointer">-</button>
                                <span class="w-7 text-center text-xs font-semibold">${item.qty}</span>
                                <button onclick="updateCartQty(${idx}, 1)" class="w-6 h-6 text-xs font-bold cursor-pointer">+</button>
                            </div>
                            <span class="text-xs font-bold">${formatPrice(subtotal)}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    const totalFinal = subtotalPrendas;

    if (subtotalEl) subtotalEl.textContent = formatPrice(subtotalPrendas);
    if (shippingLabelEl) shippingLabelEl.textContent = 'Envío';
    if (shippingEl) shippingEl.textContent = 'GRATIS';
    if (totalEl) totalEl.textContent = formatPrice(totalFinal);
}

window.updateCartQty = function(index, delta) {
    const item = state.cart[index];
    if (!item) return;
    const nextQty = item.qty + delta;
    if (nextQty <= 0) {
        state.cart.splice(index, 1);
    } else if (nextQty <= (item.maxStock || 99)) {
        item.qty = nextQty;
    }
    saveCart();
};

window.removeCartItem = function(index) {
    state.cart.splice(index, 1);
    saveCart();
};

const openCartBtn = document.getElementById('open-cart-btn');
if (openCartBtn) {
    openCartBtn.addEventListener('click', () => {
        renderCart();
        document.getElementById('cart-drawer').classList.remove('hidden');
    });
}

const closeCartBtn = document.getElementById('close-cart-btn');
if (closeCartBtn) {
    closeCartBtn.addEventListener('click', () => {
        document.getElementById('cart-drawer').classList.add('hidden');
    });
}

const cartDrawerEl = document.getElementById('cart-drawer');
if (cartDrawerEl) {
    cartDrawerEl.addEventListener('click', (e) => {
        if (e.target.id === 'cart-drawer') {
            cartDrawerEl.classList.add('hidden');
        }
    });
}

// Alternar campos según tipo de entrega y recalcular total
const entregaSelect = document.getElementById('chk-entrega');
const direccionWrapper = document.getElementById('chk-direccion-wrapper');
const provinciaWrapper = document.getElementById('chk-provincia-wrapper');

function actualizarCamposEntrega() {
    if (entregaSelect) {
        const tipo = entregaSelect.value;
        if (direccionWrapper) direccionWrapper.classList.toggle('hidden', tipo !== 'Delivery');
        if (provinciaWrapper) provinciaWrapper.classList.toggle('hidden', tipo !== 'Envío provincia');
    }
    renderCart();
}

if (entregaSelect) {
    entregaSelect.addEventListener('change', actualizarCamposEntrega);
}
actualizarCamposEntrega();

// Mostrar u ocultar datos de Yape/Plin según método de pago
const pagoSelect = document.getElementById('chk-pago');
const pagoInfoBox = document.getElementById('pago-info-box');
if (pagoSelect && pagoInfoBox) {
    pagoSelect.addEventListener('change', () => {
        pagoInfoBox.classList.toggle('hidden', pagoSelect.value === 'CONTRAENTREGA');
    });
}

const copyYapeBtn = document.getElementById('copy-yape-btn');
if (copyYapeBtn) {
    copyYapeBtn.addEventListener('click', () => {
        navigator.clipboard.writeText('987532146');
        copyYapeBtn.textContent = '¡Copiado!';
        setTimeout(() => { copyYapeBtn.textContent = 'Copiar número'; }, 2000);
    });
}

// Enviar pedido al servidor (guarda en panel) y abrir WhatsApp
const sendWhatsappBtn = document.getElementById('send-whatsapp-order-btn');
if (sendWhatsappBtn) {
    sendWhatsappBtn.addEventListener('click', async () => {
        const nombreEl = document.getElementById('chk-nombre');
        const telefonoEl = document.getElementById('chk-telefono');
        const direccionEl = document.getElementById('chk-direccion');
        const provinciaEl = document.getElementById('chk-provincia');
        const agenciaEl = document.getElementById('chk-agencia');
        const dniEl = document.getElementById('chk-dni');
        const notasEl = document.getElementById('chk-notas');

        const nombre = nombreEl ? nombreEl.value.trim() : '';
        const telefono = telefonoEl ? telefonoEl.value.trim() : '';
        const entrega = entregaSelect ? entregaSelect.value : 'Recojo en tienda';
        const direccion = direccionEl ? direccionEl.value.trim() : '';
        const provincia = provinciaEl ? provinciaEl.value.trim() : '';
        const agencia = agenciaEl ? agenciaEl.value : '';
        const dni = dniEl ? dniEl.value.trim() : '';
        const pago = pagoSelect ? pagoSelect.value : 'YAPE';
        const notas = notasEl ? notasEl.value.trim() : '';

        if (!nombre) {
            alert('Por favor escribe tu nombre para registrar tu pedido.');
            if (nombreEl) nombreEl.focus();
            return;
        }

        if (entrega === 'Envío provincia') {
            if (!provincia) {
                alert('Por favor indica tu departamento o provincia de destino.');
                if (provinciaEl) provinciaEl.focus();
                return;
            }
            if (!dni) {
                alert('Por favor ingresa el DNI del destinatario para la encomienda.');
                if (dniEl) dniEl.focus();
                return;
            }
        }

        sendWhatsappBtn.disabled = true;
        sendWhatsappBtn.textContent = 'Generando pedido...';

        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        const csrfToken = csrfInput ? csrfInput.value : '';

        try {
            const res = await fetch('/api/pedido/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    nombre,
                    telefono,
                    entrega,
                    direccion,
                    provincia,
                    agencia,
                    dni,
                    pago,
                    notas,
                    items: state.cart
                })
            });

            const data = await res.json();
            if (data.ok && data.whatsapp_url) {
                state.cart = [];
                saveCart();
                document.getElementById('cart-drawer').classList.add('hidden');
                window.open(data.whatsapp_url, '_blank');
            } else {
                alert(data.error || 'Ocurrió un problema al procesar el pedido.');
            }
        } catch (err) {
            alert('Error de conexión al enviar el pedido.');
        } finally {
            sendWhatsappBtn.disabled = false;
            sendWhatsappBtn.textContent = 'Enviar Pedido por WhatsApp →';
        }
    });
}

// =========================================================
// FILTROS Y NAVEGACIÓN DEL CATÁLOGO
// =========================================================
function setActiveCategoryStyles(activeBtn) {
    document.querySelectorAll('.cat-link').forEach(b => {
        b.classList.remove('text-black', 'dark:text-white', 'border-black', 'dark:border-white', 'font-bold');
        b.classList.add('text-neutral-500', 'dark:text-neutral-400', 'border-transparent', 'font-semibold');
    });
    activeBtn.classList.remove('text-neutral-500', 'dark:text-neutral-400', 'border-transparent', 'font-semibold');
    activeBtn.classList.add('text-black', 'dark:text-white', 'border-black', 'dark:border-white', 'font-bold');
}

document.querySelectorAll('.cat-link').forEach(btn => {
    btn.addEventListener('click', () => {
        state.onlyFavs = false;
        state.category = btn.dataset.cat;
        setActiveCategoryStyles(btn);
        renderProducts();
        const catSection = document.getElementById('catalogo');
        if (catSection) catSection.scrollIntoView({ behavior: 'smooth' });
    });
});

const toggleFilterBtn = document.getElementById('toggle-filter-btn');
if (toggleFilterBtn) {
    toggleFilterBtn.addEventListener('click', () => {
        const filterPanel = document.getElementById('filter-panel');
        if (filterPanel) filterPanel.classList.toggle('hidden');
    });
}

function setActiveSizeStyles(activeChip) {
    document.querySelectorAll('.size-chip').forEach(c => {
        c.classList.remove('bg-black', 'dark:bg-white', 'text-white', 'dark:text-black');
        c.classList.add('bg-white', 'dark:bg-[#1F1F1F]', 'border', 'border-neutral-200', 'dark:border-neutral-700', 'text-neutral-700', 'dark:text-neutral-300');
    });
    activeChip.classList.remove('bg-white', 'dark:bg-[#1F1F1F]', 'border', 'border-neutral-200', 'dark:border-neutral-700', 'text-neutral-700', 'dark:text-neutral-300');
    activeChip.classList.add('bg-black', 'dark:bg-white', 'text-white', 'dark:text-black');
}

document.querySelectorAll('.size-chip').forEach(chip => {
    chip.addEventListener('click', () => {
        state.size = chip.dataset.size;
        setActiveSizeStyles(chip);
        renderProducts();
    });
});

const searchInput = document.getElementById('search-input');
if (searchInput) {
    searchInput.addEventListener('input', (e) => {
        state.search = e.target.value;
        renderProducts();
    });
}

const navSearchBtn = document.getElementById('nav-search-btn');
if (navSearchBtn && searchInput) {
    navSearchBtn.addEventListener('click', () => {
        searchInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(() => searchInput.focus(), 300);
    });
}

const sortSelect = document.getElementById('sort-select');
if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
        state.sort = e.target.value;
        renderProducts();
    });
}

const favFilterBtn = document.getElementById('fav-filter-btn');
if (favFilterBtn) {
    favFilterBtn.addEventListener('click', () => {
        state.onlyFavs = !state.onlyFavs;
        renderProducts();
        const catSection = document.getElementById('catalogo');
        if (catSection) catSection.scrollIntoView({ behavior: 'smooth' });
    });
}

function resetAllFilters() {
    state.category = 'ALL';
    state.size = 'ALL';
    state.search = '';
    state.sort = 'featured';
    state.onlyFavs = false;
    if (searchInput) searchInput.value = '';
    if (sortSelect) sortSelect.value = 'featured';

    const allCatBtn = document.querySelector('.cat-link[data-cat="ALL"]');
    if (allCatBtn) setActiveCategoryStyles(allCatBtn);

    const allSizeChip = document.querySelector('.size-chip[data-size="ALL"]');
    if (allSizeChip) setActiveSizeStyles(allSizeChip);

    renderProducts();
}

const clearFiltersBtn = document.getElementById('clear-filters-btn');
if (clearFiltersBtn) clearFiltersBtn.addEventListener('click', resetAllFilters);

const resetAllBtn = document.getElementById('reset-all-btn');
if (resetAllBtn) resetAllBtn.addEventListener('click', resetAllFilters);

const grid4Btn = document.getElementById('grid-4-btn');
const grid3Btn = document.getElementById('grid-3-btn');

if (grid4Btn && grid3Btn && gridEl) {
    grid4Btn.addEventListener('click', () => {
        gridEl.classList.remove('lg:grid-cols-3');
        gridEl.classList.add('lg:grid-cols-4');
        grid4Btn.classList.remove('text-neutral-300', 'dark:text-neutral-600');
        grid4Btn.classList.add('text-black', 'dark:text-white');
        grid3Btn.classList.remove('text-black', 'dark:text-white');
        grid3Btn.classList.add('text-neutral-300', 'dark:text-neutral-600');
    });

    grid3Btn.addEventListener('click', () => {
        gridEl.classList.remove('lg:grid-cols-4');
        gridEl.classList.add('lg:grid-cols-3');
        grid3Btn.classList.remove('text-neutral-300', 'dark:text-neutral-600');
        grid3Btn.classList.add('text-black', 'dark:text-white');
        grid4Btn.classList.remove('text-black', 'dark:text-white');
        grid4Btn.classList.add('text-neutral-300', 'dark:text-neutral-600');
    });
}

updateCartBadge();
renderProducts();