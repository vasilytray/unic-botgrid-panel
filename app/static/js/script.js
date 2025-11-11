// app/static/js/script.js

// Система логирования
const DEBUG_LEVEL = 3; // 0 - нет логов, 1 - ошибки, 2 - предупреждения, 3 - все логи

function logError(...args) {
    if (DEBUG_LEVEL >= 1) {
        console.error('❌', ...args);
    }
}

function logWarning(...args) {
    if (DEBUG_LEVEL >= 2) {
        console.warn('⚠️', ...args);
    }
}

function logInfo(...args) {
    if (DEBUG_LEVEL >= 3) {
        console.log('ℹ️', ...args);
    }
}

function logSuccess(...args) {
    if (DEBUG_LEVEL >= 2) {
        console.log('✅', ...args);
    }
}

// Функции для работы с датами
function calculateDaysWithUs(registrationDate) {
    try {
        let regDate;
        
        // Проверяем разные форматы даты
        if (!registrationDate || registrationDate === 'None' || registrationDate === '') {
            return 0;
        }
        
        // Если это timestamp (число)
        if (!isNaN(registrationDate)) {
            regDate = new Date(parseInt(registrationDate) * 1000);
        } 
        // Если это ISO строка
        else {
            regDate = new Date(registrationDate);
        }
        
        // Проверяем валидность даты
        if (isNaN(regDate.getTime())) {
            logError('Невалидная дата регистрации:', registrationDate);
            return 0;
        }
        
        const now = new Date();
        const diffTime = now.getTime() - regDate.getTime();
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        
        return Math.max(0, diffDays);
        
    } catch (error) {
        logError('Ошибка расчета дней пользователя:', error, 'Дата:', registrationDate);
        return 0;
    }
}

function formatLastLogin(lastLoginDate) {
    if (!lastLoginDate || lastLoginDate === 'None' || lastLoginDate === '') {
        return 'Никогда';
    }
    
    try {
        let loginDate;
        
        // Обрабатываем разные форматы даты
        if (!isNaN(lastLoginDate)) {
            loginDate = new Date(parseInt(lastLoginDate) * 1000);
        } else {
            loginDate = new Date(lastLoginDate);
        }
        
        if (isNaN(loginDate.getTime())) {
            return 'Неизвестно';
        }
        
        const now = new Date();
        const diffMs = now.getTime() - loginDate.getTime();
        const diffMins = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        if (diffMins < 1) return 'Только что';
        if (diffMins < 60) return `${diffMins} мин назад`;
        if (diffHours < 24) return `${diffHours} ч назад`;
        if (diffDays === 1) return 'Вчера';
        if (diffDays < 7) return `${diffDays} дн назад`;
        
        // Для давних входов показываем полную дату
        return loginDate.toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
    } catch (error) {
        logError('Ошибка форматирования даты входа:', error, 'Дата:', lastLoginDate);
        return 'Неизвестно';
    }
}



// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', function() {
    logInfo('Загрузка приложения...');

    // Проверяем существование необходимых элементов
    const requiredElements = [
        'dynamic-content',
        'modules-container', 
        'contentTitle',
        'breadcrumb'
    ];
    
    requiredElements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            logSuccess(`✅ Элемент #${id} найден`);
        } else {
            logError(`❌ Элемент #${id} НЕ НАЙДЕН!`);
        }
    });

    initializeEventHandlers();
    
    // Создаем и тестируем ContentManager
    window.contentManager = new ContentManager();
    logInfo('ContentManager создан:', window.contentManager);
    
    // Тестируем переключение на профиль
    const profileLink = document.querySelector('[data-content="profile"]');
    if (profileLink) {
        logInfo('Ссылка на профиль найдена:', profileLink);
    } else {
        logError('Ссылка на профиль НЕ НАЙДЕНА!');
    }

    // Инициализация форм авторизации (если они есть на странице)
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('registration-form');
    
    if (loginForm) {
        logInfo('Найдена форма логина');
        loginForm.addEventListener('submit', loginFunction);
    } else {
        logError('Форма логина не найдена');
    }
    
    if (registerForm) {
        logInfo('Найдена форма регистрации');
        registerForm.addEventListener('submit', regFunction);
    } else {
        logError('Форма регистрации не найдена');
    }
    
    logSuccess('Приложение полностью инициализировано');
});

// Обработка кликов по вкладкам
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => showTab(tab.dataset.tab));
});

// Функция отображения выбранной вкладка
function showTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.form').forEach(form => form.classList.remove('active'));

    document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`${tabName}-form`).classList.add('active');
}

// Основные функции приложения
async function logoutUser() {
    try {
        logInfo('Выполнение выхода...');
        const response = await fetch('/users/logout/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });

        if (response.ok) {
            showNotification('Выход выполнен успешно', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        } else {
            const errorData = await response.json();
            logError('Ошибка при выходе:', errorData);
            showNotification('Ошибка при выходе', 'error');
        }
    } catch (error) {
        logError('Ошибка сети', error);
        showNotification('Ошибка сети', 'error');
    }
}

async function topUpBalance() {
    logInfo('Перенаправление на страницу пополнения баланса...');
    window.location.href = '/billing/topup';
}

function createNewProject() {
    logInfo('Создание нового проекта...');
    window.location.href = '/projects/create';
}

function showContent(contentType) {
    logInfo('Показать контент:', contentType);
    // В будущем можно загружать контент через AJAX
}

function navigateToService(type) {
    logInfo(`Навигация к созданию сервиса: ${type}`);
    window.location.href = `/services/${type}`;
}

// Управление сервисами
async function manageService(action, serviceId) {
    try {
        logInfo(`Управление сервисом: ${action} для ID: ${serviceId}`);
        const response = await fetch(`/services/${serviceId}/${action}`, { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include'
        });

        if (response.ok) {
            showNotification(`Сервис успешно ${getActionText(action)}`, 'success');
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } else {
            const errorData = await response.json();
            logError('Ошибка управления сервисом:', errorData);
            showNotification(errorData.detail || 'Ошибка при выполнении действия', 'error');
        }
    } catch (error) {
        logError('Error:', error);
        showNotification('Ошибка сети', 'error');
    }
}

function getActionText(action) {
    const actions = {
        'start': 'запущен',
        'stop': 'остановлен', 
        'restart': 'перезапущен',
        'start-service': 'запущен',
        'stop-service': 'остановлен'
    };
    return actions[action] || 'обновлен';
}

// Функция показа уведомлений
function showNotification(message, type) {
    // Удаляем существующие уведомления
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());

    // Создаем элемент уведомления
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        z-index: 1000;
        font-weight: bold;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        ${type === 'success' ? 'background: #28a745;' : 'background: #dc3545;'}
    `;
    
    document.body.appendChild(notification);
    
    // Удаляем уведомление через 4 секунды
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 4000);
}

// ==============================================
// ТИКЕТ СИСТЕМА - ФУНКЦИИ ДЛЯ ЧАСТИЧНЫХ СТРАНИЦ
// ==============================================

// Глобальные переменные для тикетов
window.ticketsModule = {
    currentUserPage: 1,
    currentAdminPage: 1
};

// ==================== ГЛОБАЛЬНЫЕ ОБРАБОТЧИКИ ТИКЕТОВ ====================

let currentSelectedTicket = null;

function initializeGlobalTicketHandlers() {
    logInfo('Инициализация глобальных обработчиков тикетов');
    
    // Глобальный обработчик для формы сообщений
    document.addEventListener('submit', function(e) {
        if (e.target && e.target.id === 'add-message-form') {
            e.preventDefault();
            e.stopPropagation();
            
            if (currentSelectedTicket) {
                logInfo('Обработка отправки сообщения для тикета:', currentSelectedTicket);
                handleMessageSubmit(currentSelectedTicket);
            } else {
                showNotification('Выберите обращение для отправки сообщения', 'error');
            }
        }
    });
    
    // Глобальный обработчик для кликов по тикетам
    document.addEventListener('click', function(e) {
        const ticketItem = e.target.closest('.ticket-item');
        if (ticketItem) {
            const ticketId = ticketItem.dataset.ticketId;
            if (ticketId) {
                logInfo('Открытие тикета через глобальный обработчик:', ticketId);
                openUserTicket(parseInt(ticketId));
            }
        }
    });
}

// Вызов инициализации глобальных обработчиков при загрузке DOM
document.addEventListener('DOMContentLoaded', function() {
    initializeGlobalTicketHandlers();
});

// Инициализация тикет модуля при загрузке частичных страниц
function initializeTicketsModule(moduleType) {
    logInfo(`Инициализация модуля тикетов: ${moduleType}`);
    
    switch(moduleType) {
        case 'user-tickets':
            initializeUserTickets();
            break;
        case 'admin-tickets':
            initializeAdminTickets();
            break;
    }
}

// ==================== ПОЛЬЗОВАТЕЛЬСКИЕ ТИКЕТЫ ====================

function initializeUserTickets() {
    logInfo('Инициализация пользовательских тикетов');
    loadUserTickets();
    initializeUserTicketEventHandlers();
}

function initializeUserTicketEventHandlers() {
    // Обработчик фильтра статуса
    const statusFilter = document.getElementById('status-filter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            logInfo('Фильтр статуса изменен:', this.value);
            window.ticketsModule.currentUserPage = 1;
            loadUserTickets();
        });
    }
    
    // Делегирование событий для пагинации
    const paginationContainer = document.getElementById('tickets-pagination');
    if (paginationContainer) {
        paginationContainer.addEventListener('click', function(e) {
            if (e.target.matches('.page-btn')) {
                const page = parseInt(e.target.dataset.page);
                logInfo('Переход на страницу пользовательских тикетов:', page);
                if (!isNaN(page)) {
                    window.ticketsModule.currentUserPage = page;
                    loadUserTickets(page);
                }
            }
        });
    }

    // Обработчики для модального окна создания тикета
    const createTicketModal = document.getElementById('create-ticket-modal');
    if (createTicketModal) {
        createTicketModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeCreateTicketModal();
            }
        });
    }
    
    // Обработчик формы создания тикета
    const ticketForm = document.getElementById('create-ticket-form');
    if (ticketForm) {
        ticketForm.removeEventListener('submit', submitTicketForm);
        ticketForm.addEventListener('submit', function(e) {
            console.log('Форма отправляется, предотвращаем стандартное поведение...');
            e.preventDefault();
            e.stopPropagation();
            submitTicketForm(e);
        });
    }

    // Делегирование событий для кнопок закрытия модального окна
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-action="close-create-ticket-modal"]')) {
            closeCreateTicketModal();
        }
    });
}

async function loadUserTickets(page = null) {
    if (page !== null) {
        window.ticketsModule.currentUserPage = page;
    }
    
    const currentPage = window.ticketsModule.currentUserPage;
    const statusFilter = document.getElementById('status-filter')?.value || '';
    
    logInfo(`Загрузка пользовательских тикетов, страница: ${currentPage}, фильтр: ${statusFilter}`);
    
    try {
        const response = await fetch(`/tickets/api/user/tickets?page=${currentPage}&status=${statusFilter}`, {
            credentials: 'include',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        logInfo('Статус ответа пользовательских тикетов:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        logInfo('Получены данные пользовательских тикетов:', data);
        
        renderUserTicketsList(data.tickets || []);
        renderUserPagination(data);
        
    } catch (error) {
        logError('Error loading user tickets:', error);
        showNotification('Ошибка загрузки обращений: ' + error.message, 'error');
        renderUserErrorState();
    }
}

function renderUserTicketsList(tickets) {
    const container = document.getElementById('tickets-list');
    if (!container) return;
    
    logInfo('Рендеринг пользовательских тикетов:', tickets.length);
    
    if (tickets.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-ticket-alt"></i>
                <h3>У вас пока нет обращений</h3>
                <p>Создайте первое обращение в техническую поддержку</p>
                <button class="btn-primary" data-action="create-ticket">
                    Создать новое обращение
                </button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = tickets.map(ticket => `
        <div class="ticket-item" data-ticket-id="${ticket.id}">
            <div class="ticket-title">
                <h4>${ticket.subject || 'Без темы'}</h4>
            </div>
            <div class="ticket-header">
                <span class="ticket-priority priority-${(ticket.priority || 'Medium').toLowerCase()}">
                    ${ticket.priority || 'Medium'}
                </span>
                <span class="ticket-status status-${(ticket.status || 'Open').replace(/\s/g, '').toLowerCase()}">
                    ${ticket.status || 'Open'}
                </span>
            </div>
            <div class="ticket-body">
                <div class="ticket-meta">
                    <span class="ticket-date">
                        ${ticket.updated_at ? new Date(ticket.updated_at).toLocaleDateString('ru-RU', { 
                            day: 'numeric', 
                            month: 'numeric', 
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                        }) : 'Неизвестно'}
                    </span>
                    <span class="ticket-messages">
                        ${ticket.message_count || 0} сообщений
                    </span>
                </div>
            </div>
            <!--<div class="ticket-actions">
                <button class="btn-small" data-action="open-user-ticket">
                    Открыть
                </button>
            </div>-->
        </div>
    `).join('');
}

function renderUserPagination(data) {
    const container = document.getElementById('tickets-pagination');
    if (!container) return;
    
    const totalPages = data.total_pages || 1;
    const currentPage = data.page || 1;
    
    logInfo('Рендеринг пагинации пользовательских тикетов:', { totalPages, currentPage });
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let paginationHTML = '<div class="pagination-controls">';
    
    // Кнопка "Назад"
    if (currentPage > 1) {
        paginationHTML += `<button class="page-btn" data-page="${currentPage - 1}">‹ Назад</button>`;
    }
    
    // Номера страниц
    for (let i = 1; i <= totalPages; i++) {
        if (i === currentPage) {
            paginationHTML += `<span class="current-page">${i}</span>`;
        } else {
            paginationHTML += `<button class="page-btn" data-page="${i}">${i}</button>`;
        }
    }
    
    // Кнопка "Вперед"
    if (currentPage < totalPages) {
        paginationHTML += `<button class="page-btn" data-page="${currentPage + 1}">Вперед ›</button>`;
    }
    
    paginationHTML += '</div>';
    container.innerHTML = paginationHTML;
}

function renderUserErrorState() {
    const container = document.getElementById('tickets-list');
    if (!container) return;
    
    container.innerHTML = `
        <div class="empty-state error-state">
            <i class="fas fa-exclamation-triangle"></i>
            <h3>Ошибка загрузки</h3>
            <p>Не удалось загрузить обращения. Попробуйте обновить страницу.</p>
            <button class="btn-primary" onclick="loadUserTickets()">
                <i class="fas fa-redo"></i>
                Попробовать снова
            </button>
        </div>
    `;
}

// function openUserTicket(ticketId) {
//     logInfo('Открытие пользовательского тикета в новой вкладке:', ticketId);
//     window.open(`/tickets#ticket/${ticketId}/user`, '_blank');
// }

// ==================== ФУНКЦИИ ДЛЯ ПАНЕЛИ ИСТОРИИ ТИКЕТА ====================

// let currentSelectedTicket = null;

function openUserTicket(ticketId) {
    logInfo('Открытие пользовательского тикета:', ticketId);
    
    // Снимаем выделение со всех тикетов
    document.querySelectorAll('.ticket-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Выделяем выбранный тикет
    const selectedTicket = document.querySelector(`[data-ticket-id="${ticketId}"]`);
    if (selectedTicket) {
        selectedTicket.classList.add('active');
    }
    
    // Загружаем данные тикета
    loadTicketDetails(ticketId);
    currentSelectedTicket = ticketId;
}

async function loadTicketDetails(ticketId) {
    try {
        logInfo('Загрузка деталей тикета:', ticketId);
        
        const response = await fetch(`/tickets/api/tickets/${ticketId}`, {
            credentials: 'include',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const ticket = await response.json();
        logInfo('Получены детали тикета:', ticket);
        
        renderTicketDetails(ticket);
        
    } catch (error) {
        logError('Error loading ticket details:', error);
        showNotification('Ошибка загрузки деталей обращения', 'error');
    }
}

function renderTicketDetails(ticket) {
    // Сохраняем ID текущего пользователя для определения своих сообщений
    window.currentUserId = ticket.user_id; // Или получите из другого места
    const historyPanel = document.getElementById('ticket-history-panel');
    const noTicketPanel = document.getElementById('no-ticket-selected');
    
    if (historyPanel && noTicketPanel) {
        // Показываем панель истории, скрываем сообщение о выборе
        historyPanel.style.display = 'block';
        noTicketPanel.style.display = 'none';
        
        // Заполняем информацию о тикете
        document.getElementById('ticket-subject-display').textContent = ticket.subject || 'Без темы';
        document.getElementById('ticket-id-display').textContent = `#${ticket.id}`;
        document.getElementById('ticket-priority-display').textContent = ticket.priority || 'Medium';
        document.getElementById('ticket-priority-display').className = `priority-${(ticket.priority || 'Medium').toLowerCase()}`;
        document.getElementById('ticket-status-display').textContent = ticket.status || 'Open';
        document.getElementById('ticket-status-display').className = `status-${(ticket.status || 'Open').replace(/\s/g, '').toLowerCase()}`;
        
        // Форматируем дату обновления
        const updatedAt = ticket.updated_at ? new Date(ticket.updated_at) : null;
        document.getElementById('ticket-updated-display').textContent = updatedAt ? 
            updatedAt.toLocaleDateString('ru-RU', { 
                day: 'numeric', 
                month: 'long', 
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }) : 'Неизвестно';
        
        // Рендерим историю сообщений
        renderMessageHistory(ticket.messages || []);
        
        // Настраиваем форму отправки сообщений
        setupMessageForm(ticket.id, ticket.status);
    }
}

function renderMessageHistory(messages) {
    const messageHistory = document.getElementById('message-history');
    
    if (!messages || messages.length === 0) {
        messageHistory.innerHTML = `
            <div class="empty-messages">
                <i class="fas fa-comments"></i>
                <p>Нет сообщений в истории</p>
            </div>
        `;
        return;
    }
    
    messageHistory.innerHTML = messages.map(message => {
        // Определяем отображаемое имя
        const isCurrentUser = message.sender_id === currentUserId; // Нужно получить currentUserId из глобальной переменной
        let displayName;
        
        if (isCurrentUser) {
            displayName = 'Вы';
        } else if (message.sender_name && message.sender_name !== 'Техподдержка') {
            displayName = message.sender_name;
        } else {
            displayName = 'Техподдержка';
        }
        
        return `
            <div class="message-item ${isCurrentUser ? 'user-message' : 'staff-message'}">
                <div class="message-header">
                    <span class="message-sender ${isCurrentUser ? 'user' : 'staff'}">
                        ${displayName}
                    </span>
                    <span class="message-time">
                        ${message.created_at ? new Date(message.created_at).toLocaleDateString('ru-RU', {
                            day: 'numeric',
                            month: 'long',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                        }) : 'Неизвестно'}
                    </span>
                </div>
                <div class="message-text">${message.message_text || ''}</div>
            </div>
        `;
    }).join('');
    
    // Прокручиваем к последнему сообщению
    messageHistory.scrollTop = messageHistory.scrollHeight;
}

function setupMessageForm(ticketId, ticketStatus) {
    // УПРОЩЕННАЯ ВЕРСИЯ - только управление состоянием формы
    const messageForm = document.getElementById('add-message-form');
    const messageText = document.getElementById('new-message-text');
    
    if (messageForm && messageText) {
        // Блокируем форму если тикет закрыт
        if (ticketStatus === 'Closed') {
            messageText.disabled = true;
            messageText.placeholder = 'Тикет закрыт. Новые сообщения не принимаются.';
            const submitBtn = messageForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Тикет закрыт';
            }
        } else {
            messageText.disabled = false;
            messageText.placeholder = 'Введите ваше сообщение...';
            const submitBtn = messageForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Отправить сообщение';
            }
        }
        
        // Очищаем поле ввода
        messageText.value = '';
    }
}

// Для пользователя
async function handleMessageSubmit(ticketId) {
    const messageText = document.getElementById('new-message-text');
    
    if (!messageText || !messageText.value.trim()) {
        showNotification('Введите текст сообщения', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/tickets/api/tickets/${ticketId}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                message_text: messageText.value.trim()
            }),
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        showNotification('Сообщение успешно отправлено', 'success');
        
        // Очищаем поле ввода
        messageText.value = '';
        
        // Обновляем историю сообщений
        await loadTicketDetails(ticketId);
        
        // Обновляем список тикетов
        if (typeof loadUserTickets === 'function') {
            loadUserTickets();
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        showNotification('Ошибка отправки сообщения: ' + error.message, 'error');
    }
}


// ==================== КОНЕЦ ФУНКЦИЙ ДЛЯ ПАНЕЛИ ИСТОРИИ ====================


// ==================== АДМИНСКИЕ ТИКЕТЫ ====================

function initializeAdminTickets() {
    logInfo('Инициализация админских тикетов');
    loadAdminTickets();
    loadTicketsStats();
    initializeAdminTicketEventHandlers();
}

function initializeAdminTicketEventHandlers() {
    // Обработчик применения фильтров
    const applyBtn = document.querySelector('[data-action="apply-admin-filters"]');
    if (applyBtn) {
        applyBtn.addEventListener('click', function() {
            logInfo('Применение админских фильтров...');
            window.ticketsModule.currentAdminPage = 1;
            loadAdminTickets();
        });
    }
    
    // Обработчик сброса фильтров
    const resetBtn = document.querySelector('[data-action="reset-admin-filters"]');
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            logInfo('Сброс админских фильтров...');
            document.getElementById('admin-status-filter').value = '';
            document.getElementById('admin-priority-filter').value = '';
            document.getElementById('admin-user-id-filter').value = '';
            window.ticketsModule.currentAdminPage = 1;
            loadAdminTickets();
        });
    }
    
    // Обработчик изменения количества на странице
    const pageSizeSelect = document.getElementById('admin-page-size');
    if (pageSizeSelect) {
        pageSizeSelect.addEventListener('change', function() {
            logInfo('Изменение количества тикетов на странице:', this.value);
            window.ticketsModule.currentAdminPage = 1;
            loadAdminTickets();
        });
    }
    
    // Делегирование событий для пагинации
    const paginationContainer = document.getElementById('admin-tickets-pagination');
    if (paginationContainer) {
        paginationContainer.addEventListener('click', function(e) {
            if (e.target.matches('.page-btn')) {
                const page = parseInt(e.target.dataset.page);
                logInfo('Переход на страницу админских тикетов:', page);
                if (!isNaN(page)) {
                    window.ticketsModule.currentAdminPage = page;
                    loadAdminTickets(page);
                }
            }
        });
    }
    
    // Делегирование событий для кликов по тикетам
    const ticketsList = document.getElementById('admin-tickets-list');
    const pinnedList = document.getElementById('pinned-tickets-list');
    
    [ticketsList, pinnedList].forEach(container => {
        if (container) {
            container.addEventListener('click', function(e) {
                const ticketItem = e.target.closest('.ticket-item');
                if (!ticketItem) return;
                
                const ticketId = ticketItem.dataset.ticketId;
                if (!ticketId) return;
                
                // Обработка кнопок действий в тикетах
                if (e.target.matches('[data-action]')) {
                    const action = e.target.dataset.action;
                    
                    switch(action) {
                        case 'open-admin-ticket':
                            logInfo('Открытие админского тикета:', ticketId);
                            openAdminTicket(parseInt(ticketId));
                            break;
                        case 'toggle-pin-ticket':
                            const currentPinState = ticketItem.classList.contains('pinned');
                            logInfo('Переключение закрепления тикета:', ticketId, 'новое состояние:', !currentPinState);
                            togglePinTicket(parseInt(ticketId), !currentPinState);
                            break;
                    }
                }
            });
        }
    });
}

async function loadAdminTickets(page = null) {
    if (page !== null) {
        window.ticketsModule.currentAdminPage = page;
    }
    
    const currentPage = window.ticketsModule.currentAdminPage;
    const statusFilter = document.getElementById('admin-status-filter')?.value || '';
    const priorityFilter = document.getElementById('admin-priority-filter')?.value || '';
    const userIdFilter = document.getElementById('admin-user-id-filter')?.value || '';
    const pageSize = document.getElementById('admin-page-size')?.value || '25';
    
    logInfo(`Загрузка админских тикетов, страница: ${currentPage}, размер: ${pageSize}`);
    
    try {
        let url = `/tickets/api/admin/tickets?page=${currentPage}&page_size=${pageSize}`;
        if (statusFilter) url += `&status=${statusFilter}`;
        if (priorityFilter) url += `&priority=${priorityFilter}`;
        if (userIdFilter) url += `&user_id=${userIdFilter}`;
        
        logInfo('URL запроса админских тикетов:', url);
        
        const response = await fetch(url, {
            credentials: 'include',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        logInfo('Статус ответа админских тикетов:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        logInfo('Получены данные админских тикетов:', data);
        
        renderAdminTicketsList(data.tickets || []);
        renderAdminPagination(data);
        updateTicketsCounters(data);
        
    } catch (error) {
        logError('Error loading admin tickets:', error);
        showNotification('Ошибка загрузки обращений: ' + error.message, 'error');
        renderAdminErrorState();
    }
}

function renderAdminTicketsList(tickets) {
    const regularContainer = document.getElementById('admin-tickets-list');
    const pinnedContainer = document.getElementById('pinned-tickets-list');
    const pinnedSection = document.getElementById('pinned-tickets-section');
    
    if (!regularContainer || !pinnedContainer) return;
    
    logInfo('Рендеринг админских тикетов:', tickets.length);
    
    // Разделяем тикеты на закрепленные и обычные
    const pinnedTickets = tickets.filter(ticket => ticket.is_pinned);
    const regularTickets = tickets.filter(ticket => !ticket.is_pinned);
    
    logInfo(`Закрепленные: ${pinnedTickets.length}, Обычные: ${regularTickets.length}`);
    
    // Показываем/скрываем секцию закрепленных тикетов
    if (pinnedTickets.length > 0) {
        pinnedSection.style.display = 'block';
        renderTicketsToContainer(pinnedTickets, pinnedContainer, true);
    } else {
        pinnedSection.style.display = 'none';
        pinnedContainer.innerHTML = '';
    }
    
    // Рендерим обычные тикеты
    if (regularTickets.length === 0 && pinnedTickets.length === 0) {
        regularContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-ticket-alt"></i>
                <h3>Обращения не найдены</h3>
                <p>Попробуйте изменить параметры фильтрации</p>
            </div>
        `;
    } else {
        renderTicketsToContainer(regularTickets, regularContainer, false);
    }
}

function renderTicketsToContainer(tickets, container, isPinned) {
    if (tickets.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <p>${isPinned ? 'Нет закрепленных обращений' : 'Нет обращений'}</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = tickets.map(ticket => `
        <div class="ticket-item ${ticket.is_pinned ? 'pinned' : ''}" data-ticket-id="${ticket.id}">
            <div class="ticket-header">
                <div class="ticket-title">
                    ${ticket.is_pinned ? '<i class="fas fa-thumbtack" title="Закреплено"></i>' : ''}
                    ID: <h4>${ticket.id || 'Без номера'}</h4>
                    ТЕМА: <h4>${ticket.subject || 'Без темы'}</h4>
                </div>
                <div class="ticket-badges">
                    <span class="ticket-priority priority-${(ticket.priority || 'Medium').toLowerCase()}">
                        ${ticket.priority || 'Medium'}
                    </span>
                    <span class="ticket-user">UID:${ticket.user_id || 'Неизвестно'}</span>
                </div>
            </div>
            <div class="ticket-body-action">
            <div class="ticket-body">
                <div class="ticket-meta">
                    <span class="ticket-status status-${(ticket.status || 'Open').replace(/\s/g, '').toLowerCase()}">
                        ${ticket.status || 'Open'}
                    </span>
                    <span class="ticket-date">
                        ${ticket.updated_at ? new Date(ticket.updated_at).toLocaleDateString('ru-RU') : 'Неизвестно'}
                    </span>
                    <span class="ticket-messages">
                        ${ticket.message_count || 0} сообщений
                    </span>
                </div>
            </div>
            <div class="ticket-actions">
                <button class="btn-small" data-action="open-admin-ticket">
                    Управление
                </button>
                <button class="btn-small ${ticket.is_pinned ? 'pin-toggle-btn' : 'pin-toggle-btn'}" 
                        data-action="toggle-pin-ticket">
                    ${ticket.is_pinned ? '📌' : '📍'}
                </button>
            </div>
            </div>
        </div>
    `).join('');
}

function updateTicketsCounters(data) {
    const tickets = data.tickets || [];
    const pinnedCount = tickets.filter(t => t.is_pinned).length;
    const regularCount = tickets.length - pinnedCount;
    const totalCount = data.total_count || 0;
    
    // Обновляем счетчики в секциях
    const pinnedCountElement = document.getElementById('pinned-count');
    const regularCountElement = document.getElementById('regular-count');
    
    if (pinnedCountElement) pinnedCountElement.textContent = pinnedCount;
    if (regularCountElement) regularCountElement.textContent = regularCount;
    
    // Обновляем информацию в футере
    const shownTicketsElement = document.getElementById('shown-tickets');
    const totalTicketsCountElement = document.getElementById('total-tickets-count');
    
    if (shownTicketsElement) shownTicketsElement.textContent = tickets.length;
    if (totalTicketsCountElement) totalTicketsCountElement.textContent = Math.min(totalCount, 300);
    
    // Обновляем статистику
    const pinnedStatsElement = document.getElementById('pinned-tickets');
    if (pinnedStatsElement) {
        pinnedStatsElement.textContent = `${pinnedCount} закреплено`;
    }
}

function renderAdminPagination(data) {
    const container = document.getElementById('admin-tickets-pagination');
    if (!container) return;
    
    const totalPages = data.total_pages || 1;
    const currentPage = data.page || 1;
    const totalCount = data.total_count || 0;
    
    logInfo('Рендеринг пагинации админских тикетов:', { totalPages, currentPage, totalCount });
    
    // Ограничиваем общее количество тикетов 300
    const maxTotalTickets = Math.min(totalCount, 300);
    const maxPages = Math.ceil(maxTotalTickets / (data.page_size || 25));
    const effectiveTotalPages = Math.min(totalPages, maxPages);
    
    if (effectiveTotalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let paginationHTML = '<div class="pagination-controls">';
    
    // Кнопка "Назад"
    if (currentPage > 1) {
        paginationHTML += `<button class="page-btn" data-page="${currentPage - 1}">‹ Назад</button>`;
    }
    
    // Номера страниц (максимум 5 страниц вокруг текущей)
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(effectiveTotalPages, currentPage + 2);
    
    if (startPage > 1) {
        paginationHTML += `<button class="page-btn" data-page="1">1</button>`;
        if (startPage > 2) paginationHTML += `<span class="page-info">...</span>`;
    }
    
    for (let i = startPage; i <= endPage; i++) {
        if (i === currentPage) {
            paginationHTML += `<span class="current-page">${i}</span>`;
        } else {
            paginationHTML += `<button class="page-btn" data-page="${i}">${i}</button>`;
        }
    }
    
    if (endPage < effectiveTotalPages) {
        if (endPage < effectiveTotalPages - 1) paginationHTML += `<span class="page-info">...</span>`;
        paginationHTML += `<button class="page-btn" data-page="${effectiveTotalPages}">${effectiveTotalPages}</button>`;
    }
    
    // Кнопка "Вперед"
    if (currentPage < effectiveTotalPages) {
        paginationHTML += `<button class="page-btn" data-page="${currentPage + 1}">Вперед ›</button>`;
    }
    
    paginationHTML += '</div>';
    container.innerHTML = paginationHTML;
}

// Обновите функцию загрузки статистики
async function loadTicketsStats() {
    try {
        logInfo('Загрузка статистики тикетов...');
        const response = await fetch('/tickets/api/tickets/stats', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const stats = await response.json();
            logInfo('Статистика тикетов:', stats);
            
            document.getElementById('total-tickets').textContent = `${Math.min(stats.total || 0, 300)} всего`;
            document.getElementById('open-tickets').textContent = `${stats.by_status?.Open || 0} открыто`;
            
            // Считаем закрепленные тикеты
            const pinnedCount = await getPinnedTicketsCount();
            document.getElementById('pinned-tickets').textContent = `${pinnedCount} закреплено`;
            
        } else {
            logError('Ошибка загрузки статистики:', response.status);
        }
    } catch (error) {
        logError('Error loading stats:', error);
    }
}

// Вспомогательная функция для подсчета закрепленных тикетов
async function getPinnedTicketsCount() {
    try {
        const response = await fetch('/tickets/api/admin/tickets?page=1&page_size=1&is_pinned=true', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            return data.total_count || 0;
        }
    } catch (error) {
        logError('Error counting pinned tickets:', error);
    }
    return 0;
}

function renderAdminErrorState() {
    const container = document.getElementById('admin-tickets-list');
    if (!container) return;
    
    container.innerHTML = `
        <div class="empty-state error-state">
            <i class="fas fa-exclamation-triangle"></i>
            <h3>Ошибка загрузки</h3>
            <p>Не удалось загрузить обращения. Попробуйте обновить страницу.</p>
            <button class="btn-primary" onclick="loadAdminTickets()">
                <i class="fas fa-redo"></i>
                Попробовать снова
            </button>
        </div>
    `;
}

function openAdminTicket(ticketId) {
    logInfo('Открытие админского тикета:', ticketId);
    
    // Сохраняем ID тикета в глобальной переменной
    window.currentTicketId = ticketId;
    
    // Показываем модуль управления тикетом
    if (window.contentManager) {
        // Добавьте модуль в ContentManager
        if (!window.contentManager.modules.has('admin-ticket-request')) {
            window.contentManager.modules.set('admin-ticket-request', {
                title: 'Управление обращением',
                breadcrumb: ['Главная', 'Администрирование', 'Обращения', 'Управление'],
                type: 'partial',
                url: '/partials/tickets/admin_ticket_request'
            });
        }
        window.contentManager.showModule('admin-ticket-request');
    } else {
        // Fallback: открываем в новой вкладке
        window.open(`/tickets/admin#ticket/${ticketId}`, '_blank');
    }
}

async function togglePinTicket(ticketId, pinState) {
    try {
        logInfo('Обновление закрепления тикета:', ticketId, pinState);
        
        const response = await fetch(`/tickets/api/tickets/${ticketId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                is_pinned: pinState
            })
        });
        
        if (response.ok) {
            showNotification(`Тикет ${pinState ? 'закреплен' : 'откреплен'}`, 'success');
            
            // ОБНОВЛЯЕМ UI НА СТРАНИЦЕ УПРАВЛЕНИЯ ТИКЕТОМ
            if (document.getElementById('pin-ticket-btn')) {
                updatePinButtonState(pinState);
            }
            
            // ОБНОВЛЯЕМ СПИСОК ТИКЕТОВ (если мы на странице списка)
            if (typeof loadAdminTickets === 'function') {
                loadAdminTickets();
            }
        } else {
            const errorData = await response.json();
            logError('Ошибка обновления тикета:', errorData);
            showNotification('Ошибка обновления тикета', 'error');
        }
    } catch (error) {
        logError('Error toggling pin:', error);
        showNotification('Ошибка обновления тикета', 'error');
    }
}

// ==================== АДМИНСКАЯ СТРАНИЦА УПРАВЛЕНИЯ ТИКЕТОМ ====================

function initializeAdminTicketPage() {
    console.log('🔄 Инициализация страницы управления тикетом...');
    
    // Получаем ID тикета из URL или глобальной переменной
    const urlParams = new URLSearchParams(window.location.search);
    const ticketId = urlParams.get('ticketId') || window.currentTicketId;
    
    if (!ticketId) {
        console.error('❌ ID тикета не указан');
        showNotification('ID тикета не указан', 'error');
        return;
    }
    
    console.log('Загрузка тикета:', ticketId);
    loadAdminTicketDetail(ticketId);
    setupAdminTicketEventHandlers(ticketId);
}

function setupAdminTicketEventHandlers(ticketId) {
    console.log('🔄 Настройка обработчиков для тикета:', ticketId);
    
    // Кнопка "Назад к списку"
    const backBtn = document.getElementById('back-to-tickets-list');
    if (backBtn) {
        backBtn.addEventListener('click', function() {
            console.log('← Назад к списку тикетов');
            if (window.contentManager) {
                window.contentManager.showModule('admin-tickets');
            } else {
                window.history.back();
            }
        });
    }
    
    // Сохранение изменений
    const saveBtn = document.getElementById('save-ticket-changes');
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            console.log('💾 Сохранение изменений тикета:', ticketId);
            updateAdminTicket(ticketId);
        });
    }
    
    // Быстрые действия
    const pinBtn = document.getElementById('pin-ticket-btn');
    if (pinBtn) {
        // Удаляем старый обработчик и добавляем новый
        pinBtn.replaceWith(pinBtn.cloneNode(true));
        const newPinBtn = document.getElementById('pin-ticket-btn');
        
        newPinBtn.addEventListener('click', function() {
            // Определяем текущее состояние по классам кнопки
            const isCurrentlyPinned = this.classList.contains('btn-secondary');
            const newPinState = !isCurrentlyPinned;
            
            console.log('📌 Переключение закрепления:', ticketId, 'новое состояние:', newPinState);
            togglePinTicket(ticketId, newPinState);
        });
    }
    
    const closeBtn = document.getElementById('close-ticket-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            console.log('🔒 Закрытие тикета:', ticketId);
            closeAdminTicket(ticketId);
        });
    }
    
    // Форма ответа
    const replyForm = document.getElementById('admin-reply-form');
    if (replyForm) {
        replyForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('📤 Отправка ответа для тикета:', ticketId);
            handleAdminReply(ticketId);
        });
    }
    
    // Предпросмотр сообщения
    const previewBtn = document.getElementById('preview-message');
    if (previewBtn) {
        previewBtn.addEventListener('click', function() {
            console.log('👀 Предпросмотр сообщения');
            previewAdminMessage();
        });
    }
    
    console.log('✅ Обработчики настроены для тикета:', ticketId);
}

async function loadAdminTicketDetail(ticketId) {
    try {
        console.log('📥 Загрузка деталей тикета для админа:', ticketId);
        
        const response = await fetch(`/tickets/api/tickets/${ticketId}`, {
            credentials: 'include',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        console.log('📨 Ответ сервера:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const ticket = await response.json();
        console.log('✅ Получены детали тикета:', ticket);
        
        renderAdminTicketDetail(ticket);
        
    } catch (error) {
        console.error('❌ Error loading admin ticket details:', error);
        showNotification('Ошибка загрузки деталей обращения', 'error');
    }
}

function renderAdminTicketDetail(ticket) {
    console.log('🎨 Рендеринг деталей тикета:', ticket.id);
    
    // Основная информация
    const ticketIdDisplay = document.getElementById('ticket-id-display');
    const ticketSubject = document.getElementById('ticket-subject-display');
    const ticketUserInfo = document.getElementById('ticket-user-info');
    const ticketCreatedAt = document.getElementById('ticket-created-at');
    const ticketUpdatedAt = document.getElementById('ticket-updated-at');
    const ticketMessagesCount = document.getElementById('ticket-messages-count');
    const ticketDescription = document.getElementById('ticket-description-content');
    const firstMessageTime = document.getElementById('first-message-time');
    const ticketIdMeta = document.getElementById('ticket-id-meta');
    const conversationCount = document.getElementById('conversation-count');
    
    if (ticketIdDisplay) ticketIdDisplay.textContent = ticket.id;
    if (ticketSubject) ticketSubject.textContent = ticket.subject || 'Без темы';
    if (ticketUserInfo) ticketUserInfo.textContent = `UID: ${ticket.user_id} (${ticket.user_nick || ticket.user_email})`; // Используем user_nick
    if (ticketCreatedAt) ticketCreatedAt.textContent = formatDetailedDate(ticket.created_at);
    if (ticketUpdatedAt) ticketUpdatedAt.textContent = formatDetailedDate(ticket.updated_at);
    if (ticketMessagesCount) ticketMessagesCount.textContent = ticket.message_count || 0;
    if (ticketIdMeta) ticketIdMeta.textContent = `#${ticket.id}`;

    // Вместо описания тикета показываем первое сообщение
    if (ticketDescription) {
        // Ищем первое сообщение пользователя
        const firstUserMessage = ticket.messages?.find(msg => 
            msg.sender_id === ticket.user_id
        );
        
        if (firstUserMessage) {
            ticketDescription.textContent = firstUserMessage.message_text || 'Нет сообщения';
            if (firstMessageTime) {
                firstMessageTime.textContent = formatDetailedDate(firstUserMessage.created_at);
            }
        } else {
            // Fallback на описание тикета
            ticketDescription.textContent = ticket.description || 'Нет описания проблемы';
            if (firstMessageTime) {
                firstMessageTime.textContent = formatDetailedDate(ticket.created_at);
            }
        }
    }
    
    if (conversationCount) conversationCount.textContent = `${ticket.messages?.length || 0} сообщений`;
    
    // Остальной код остается без изменений...
    const statusSelect = document.getElementById('ticket-status-select');
    const prioritySelect = document.getElementById('ticket-priority-select');
    
    if (statusSelect) {
        statusSelect.value = ticket.status || 'Open';
        console.log('🎯 Установлен статус:', ticket.status);
    }
    if (prioritySelect) {
        prioritySelect.value = ticket.priority || 'Medium';
        console.log('🎯 Установлен приоритет:', ticket.priority);
    }
    
    // Бейджи
    updateStatusBadge(ticket.status);
    updatePriorityBadge(ticket.priority);

    // ОБНОВЛЯЕМ КНОПКУ ЗАКРЕПЛЕНИЯ
    updatePinButtonState(ticket.is_pinned);

    // ОБНОВЛЯЕМ ВИДИМОСТЬ КНОПКИ ЗАКРЫТИЯ
    updateCloseButtonVisibility(ticket.status);
    
    // История сообщений
    renderAdminMessageHistory(ticket.messages || [], ticket.user_id);
    
    console.log('✅ Детали тикета отрендерены');
}

// Добавляем функцию для обновления состояния кнопки закрепления
function updatePinButtonState(isPinned) {
    const pinBtn = document.getElementById('pin-ticket-btn');
    if (!pinBtn) return;
    
    if (isPinned) {
        pinBtn.innerHTML = '📌';
        pinBtn.classList.remove('btn-warning');
        pinBtn.classList.add('btn-secondary');
        pinBtn.title = 'Открепить обращение';
    } else {
        pinBtn.innerHTML = '📍';
        pinBtn.classList.remove('btn-secondary');
        pinBtn.classList.add('btn-warning');
        pinBtn.title = 'Закрепить обращение';
    }
    
    console.log('📌 Состояние кнопки закрепления обновлено:', isPinned ? 'закреплен' : 'откреплен');
}

// Добавляем функцию для управления видимостью кнопки закрытия
function updateCloseButtonVisibility(ticketStatus) {
    const closeBtn = document.getElementById('close-ticket-btn');
    if (!closeBtn) return;
    
    const isClosed = ticketStatus === 'Closed';
    
    if (isClosed) {
        closeBtn.style.display = 'none';
        console.log('🔒 Кнопка закрытия скрыта - тикет уже закрыт');
    } else {
        closeBtn.style.display = 'flex'; // или 'inline-flex' в зависимости от вашего стиля
        console.log('🔓 Кнопка закрытия отображена - тикет открыт');
    }
}

function renderAdminMessageHistory(messages, ticketUserId) {
    const container = document.getElementById('message-history');
    
    if (!container) return;
    
    if (!messages || messages.length === 0) {
        container.innerHTML = `<div class="no-messages"><i class="fas fa-comments"></i><p>Нет сообщений в истории</p></div>`;
        return;
    }
    
    try {
        container.innerHTML = messages.map(message => {
            // Используем флаг is_tech_support из базы данных
            const isTechSupport = message.is_tech_support;
            const isStaff = message.sender_id !== ticketUserId; // Админ/модератор
            
            let displayName;
            if (isTechSupport) {
                displayName = 'Техподдержка';
            } else if (isStaff) {
                // Админ ответил от своего имени
                displayName = message.sender_name || 'Администратор';
            } else {
                // Обычный пользователь
                displayName = message.sender_name || 'Пользователь';
            }
            
            const messageClass = isStaff ? 'staff-message' : 'user-message';
            const senderClass = isStaff ? 'staff' : 'user';
            
            return `
                <div class="message-item ${messageClass}">
                    <div class="message-header">
                        <span class="message-sender ${senderClass}">
                            ${displayName}
                            ${isTechSupport ? ' 🔧' : ''}
                        </span>
                        <span class="message-time">
                            ${formatDetailedDate(message.created_at)}
                        </span>
                    </div>
                    <div class="message-text">${message.message_text || ''}</div>
                    <div class="message-meta">
                        <small>ID сообщения: ${message.id}</small>
                        ${isTechSupport ? '<small class="tech-support-badge">🔧 От имени техподдержки</small>' : ''}
                    </div>
                </div>
            `;
        }).join('');
        
        container.scrollTop = container.scrollHeight;
        console.log('✅ История сообщений отрендерена');
    } catch (error) {
        console.error('❌ Ошибка при рендеринге истории сообщений:', error);
        container.innerHTML = `<div class="error-state"><p>Ошибка загрузки истории</p></div>`;
    }
}

async function updateAdminTicket(ticketId) {
    const status = document.getElementById('ticket-status-select')?.value;
    const priority = document.getElementById('ticket-priority-select')?.value;
    
    console.log('🔄 Обновление тикета:', { ticketId, status, priority });
    
    try {
        const response = await fetch(`/tickets/api/tickets/${ticketId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                status: status,
                priority: priority
            }),
            credentials: 'include'
        });
        
        console.log('📨 Ответ обновления:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const updatedTicket = await response.json();
        showNotification('Настройки обращения обновлены', 'success');
        
        // Обновляем UI
        updateStatusBadge(updatedTicket.status);
        updatePriorityBadge(updatedTicket.priority);

        // ОБНОВЛЯЕМ ВИДИМОСТЬ КНОПКИ ЗАКРЫТИЯ
        updateCloseButtonVisibility(updatedTicket.status);
        
        console.log('✅ Тикет обновлен:', updatedTicket);
        
    } catch (error) {
        console.error('❌ Error updating ticket:', error);
        showNotification('Ошибка обновления обращения: ' + error.message, 'error');
    }
}

// Для администратора
async function handleAdminReply(ticketId) {
    const messageText = document.getElementById('admin-message-text')?.value.trim();
    const changeStatus = document.getElementById('change-status-on-reply')?.checked;
    
    if (!messageText) {
        showNotification('Введите текст сообщения', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/tickets/api/tickets/${ticketId}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                message_text: messageText
            }),
            credentials: 'include'
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        showNotification('Сообщение отправлено', 'success');
        document.getElementById('admin-message-text').value = '';
        await loadAdminTicketDetail(ticketId);
        
        if (changeStatus) {
            await fetch(`/tickets/api/tickets/${ticketId}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({status: 'Awaiting User Response'}),
                credentials: 'include'
            });
        }
        
    } catch (error) {
        console.error('Error sending admin reply:', error);
        showNotification('Ошибка отправки сообщения: ' + error.message, 'error');
    }
}

function updateStatusBadge(status) {
    const badge = document.getElementById('current-status-badge');
    if (badge) {
        badge.textContent = status;
        badge.className = 'status-badge status-' + status.replace(/\s/g, '');
        console.log('🎯 Обновлен бейдж статуса:', status);
    }
}

function updatePriorityBadge(priority) {
    const badge = document.getElementById('current-priority-badge');
    if (badge) {
        badge.textContent = priority;
        badge.className = 'priority-badge priority-' + priority;
        console.log('🎯 Обновлен бейдж приоритета:', priority);
    }
}

function formatDetailedDate(dateString) {
    if (!dateString) return 'Неизвестно';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            day: 'numeric',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (error) {
        console.error('❌ Ошибка форматирования даты:', dateString, error);
        return 'Неизвестно';
    }
}

function previewAdminMessage() {
    const messageText = document.getElementById('admin-message-text')?.value.trim();
    
    if (!messageText) {
        showNotification('Введите текст для предпросмотра', 'error');
        return;
    }
    
    // Создаем или обновляем блок предпросмотра
    let preview = document.getElementById('message-preview');
    if (!preview) {
        preview = document.createElement('div');
        preview.id = 'message-preview';
        preview.className = 'message-preview';
        const formOptions = document.querySelector('.form-options');
        if (formOptions) {
            formOptions.parentNode.insertBefore(preview, formOptions);
        }
    }
    
    preview.innerHTML = `
        <div class="preview-header">
            Предпросмотр сообщения
            <button class="preview-close" onclick="this.parentElement.parentElement.classList.remove('show')">×</button>
        </div>
        <div class="preview-content">${messageText}</div>
    `;
    
    preview.classList.add('show');
    console.log('👀 Показан предпросмотр сообщения');
}

async function closeAdminTicket(ticketId) {
    console.log('🔒 Закрытие тикета:', ticketId);
    
    try {
        const response = await fetch(`/tickets/api/tickets/${ticketId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                status: 'Closed'
            }),
            credentials: 'include'
        });
        
        console.log('📨 Ответ закрытия тикета:', response.status);
        
        if (response.ok) {
            showNotification('Обращение закрыто', 'success');
            
            // ОБНОВЛЯЕМ ВИДИМОСТЬ КНОПКИ ЗАКРЫТИЯ
            updateCloseButtonVisibility('Closed');
            
            // Обновляем статус в селекторе
            const statusSelect = document.getElementById('ticket-status-select');
            if (statusSelect) {
                statusSelect.value = 'Closed';
            }
            
            // Обновляем бейдж статуса
            updateStatusBadge('Closed');
            
            // Перезагружаем детали тикета для полного обновления UI
            await loadAdminTicketDetail(ticketId);
            
            console.log('✅ Тикет закрыт, UI обновлен');
        } else {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
    } catch (error) {
        console.error('❌ Error closing ticket:', error);
        showNotification('Ошибка закрытия обращения: ' + error.message, 'error');
    }
}

// ==================== КОНЕЦ ФУНКЦИЙ ДЛЯ АДМИНИСТРИРОВАНИЯ ТИКЕТОВ ====================

// Система динамических модулей с TTL-кэшированием
class ContentManager {
    constructor() {
        this.currentModule = 'dashboard';
        this.modules = new Map();
        this.moduleCache = new Map(); // { html: string, timestamp: number }
        this.initializeModules();
    }

    initializeModules() {
        // Регистрируем модули
        this.modules.set('dashboard', {
            title: 'Панель управления',
            breadcrumb: ['Главная', 'Панель управления'],
            type: 'internal'
        });
        
        this.modules.set('all-services', {
            title: 'Все сервисы',
            breadcrumb: ['Главная', 'Сервисы', 'Все сервисы'],
            type: 'partial',
            url: '/partials/services/all'
        });
        
        this.modules.set('vps-services', {
            title: 'VPS сервисы',
            breadcrumb: ['Главная', 'Сервисы', 'VPS'],
            type: 'partial',
            url: '/partials/services/vps'
        });

        this.modules.set('docker-services', {
            title: 'Docker сервисы', 
            breadcrumb: ['Главная', 'Сервисы', 'Docker'],
            type: 'partial',
            url: '/partials/services/docker'
        });
        
        this.modules.set('n8n-services', {
            title: 'n8n сервисы',
            breadcrumb: ['Главная', 'Сервисы', 'n8n'],
            type: 'partial',
            url: '/partials/services/n8n'
        });
        
        this.modules.set('invoices', {
            title: 'Счета и платежи',
            breadcrumb: ['Главная', 'Финансы', 'Счета и платежи'],
            type: 'partial',
            url: '/partials/invoices'
        });
        
        this.modules.set('billing-history', {
            title: 'История операций',
            breadcrumb: ['Главная', 'Финансы', 'История операций'],
            type: 'partial',
            url: '/partials/billing/history'
        });
        
        this.modules.set('projects', {
            title: 'Мои проекты',
            breadcrumb: ['Главная', 'Проекты', 'Мои проекты'],
            type: 'partial',
            url: '/partials/projects'
        });

        this.modules.set('profile', {
            title: 'Профиль пользователя',
            breadcrumb: ['Главная', 'Профиль'],
            type: 'partial',
            url: '/partials/profile'
        });

        this.modules.set('edit-basic-profile', {
            title: 'Редактирование профиля',
            breadcrumb: ['Главная', 'Профиль', 'Редактирование'],
            type: 'partial',
            url: '/partials/edit-basic-profile'
        });

        this.modules.set('edit-password', {
            title: 'Смена пароля',
            breadcrumb: ['Главная', 'Профиль', 'Смена пароля'],
            type: 'partial', 
            url: '/partials/edit-password'
        });

        this.modules.set('edit-security', {
            title: 'Управление безопасностью',
            breadcrumb: ['Главная', 'Профиль', 'Безопасность'],
            type: 'partial',
            url: '/partials/edit-security'
        });

        this.modules.set('user-tickets', {
            title: 'Мои обращения',
            breadcrumb: ['Главная', 'Поддержка', 'Мои обращения'],
            type: 'partial',
            url: '/partials/tickets/user'
        });

        this.modules.set('admin-tickets', {
            title: 'Управление обращениями',
            breadcrumb: ['Главная', 'Администрирование', 'Обращения'],
            type: 'partial', 
            url: '/partials/tickets/admin'
        });
    }

    async showModule(moduleId) {
        logInfo(`🔄 Показ модуля: ${moduleId}`);
        
        // Всегда обновляем UI и навигацию
        this.updateUI(moduleId);
        this.updateActiveNav(moduleId);
        
        try {
            const module = this.modules.get(moduleId);
            if (!module) {
                throw new Error(`Модуль ${moduleId} не найден`);
            }
            
            if (moduleId === 'dashboard') {
                await this.showDashboard();
            } else if (module.type === 'partial') {
                // Для критичных модулей всегда свежие данные
                if (this.shouldForceReload(moduleId)) {
                    this.moduleCache.delete(moduleId);
                }
                
                await this.loadPartialPage(moduleId, module.url);
            }
            
            this.currentModule = moduleId;
            logSuccess(`✅ Модуль ${moduleId} успешно показан`);
            
        } catch (error) {
            logError(`❌ Ошибка загрузки модуля ${moduleId}:`, error);
            this.showError(moduleId, error);
        }
    }

    shouldForceReload(moduleId) {
        // Всегда свежие данные для этих модулей
        const forceReloadModules = ['profile', 'invoices', 'billing-history'];
        return forceReloadModules.includes(moduleId);
    }

    isCacheValid(moduleId) {
        const cache = this.moduleCache.get(moduleId);
        if (!cache) return false;
        
        const cacheAge = Date.now() - cache.timestamp;
        const ttl = this.getModuleTTL(moduleId);
        
        return cacheAge < ttl;
    }

    getModuleTTL(moduleId) {
        // Время жизни кэша для разных модулей (в миллисекундах)
        const ttlConfig = {
            'profile': 30000,        // 30 секунд
            'invoices': 60000,       // 1 минута
            'billing-history': 60000, // 1 минута
            'all-services': 45000,   // 45 секунд
            'vps-services': 45000,
            'docker-services': 45000,
            'n8n-services': 45000,
            'projects': 60000,
            'default': 30000         // 30 секунд по умолчанию
        };
        
        return ttlConfig[moduleId] || ttlConfig.default;
    }

    async loadPartialPage(moduleId, url) {
        // Проверяем валидность кэша
        if (this.isCacheValid(moduleId)) {
            logInfo(`📤 Используем кэш для модуля: ${moduleId}`);
            this.showCachedModule(moduleId);
            return;
        }

        logInfo(`📥 Загрузка частичной страницы: ${url}`);
        this.showLoading(moduleId);
        
        try {
            const response = await fetch(url, {
                credentials: 'include',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'text/html'
                }
            });
            
            logInfo(`Статус ответа: ${response.status} ${response.statusText}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const html = await response.text();
            logInfo(`Получен HTML длиной: ${html.length} символов`);
            
            // Обрабатываем специальные данные для профиля
            let processedHtml = html;
            if (moduleId === 'profile') {
                processedHtml = this.processProfileData(html);
            }
            
            // Сохраняем в кэш
            this.moduleCache.set(moduleId, {
                html: processedHtml,
                timestamp: Date.now()
            });
            
            this.renderPartial(moduleId, processedHtml);
            logSuccess(`✅ Модуль ${moduleId} загружен и закэширован`);
            
        } catch (error) {
            logError(`❌ Ошибка загрузки частичной страницы:`, error);
            
            // Пытаемся показать устаревший кэш при ошибке
            const cache = this.moduleCache.get(moduleId);
            if (cache) {
                logWarning(`⚠️ Показываем устаревший кэш из-за ошибки: ${moduleId}`);
                this.showCachedModule(moduleId);
            } else {
                throw new Error(`Не удалось загрузить частичную страницу: ${error.message}`);
            }
        }
    }

    processProfileData(html) {
        try {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            
            // Отладочная информация
            const registrationElement = tempDiv.querySelector('[data-registration-date]');
            const lastLoginElement = tempDiv.querySelector('[data-last-login]');
            
            logInfo('Найден элемент регистрации:', registrationElement);
            logInfo('Найден элемент последнего входа:', lastLoginElement);
            
            if (registrationElement) {
                const regDate = registrationElement.dataset.registrationDate;
                logInfo('Дата регистрации из data-атрибута:', regDate);
                
                const daysWithUs = calculateDaysWithUs(regDate);
                const daysElement = tempDiv.querySelector('#days-with-us');
                if (daysElement) {
                    daysElement.textContent = daysWithUs + ' дней';
                    logSuccess('Установлено дней с нами:', daysWithUs);
                }
            }
            
            if (lastLoginElement) {
            const loginDate = lastLoginElement.dataset.lastLogin;
            logInfo('⏰ Дата последнего входа из data-атрибута:', loginDate);
            
            // Проверяем, что дата не пустая
            if (loginDate && loginDate !== '') {
                const formattedLogin = formatLastLogin(loginDate);
                const loginElement = tempDiv.querySelector('#last-login-time');
                if (loginElement) {
                    loginElement.textContent = formattedLogin;
                    logSuccess('✅ Установлено время входа:', formattedLogin);
                }
            } else {
                logWarning('⚠️ Дата последнего входа пустая или отсутствует');
                const loginElement = tempDiv.querySelector('#last-login-time');
                if (loginElement) {
                    loginElement.textContent = 'Никогда';
                }
            }
        }

            // Автоматически проверяем IP при загрузке профиля
            setTimeout(() => {
                if (typeof checkCurrentIP === 'function') {
                    checkCurrentIP();
                }
            }, 500);
            
            return tempDiv.innerHTML;
        } catch (error) {
            logError('Ошибка обработки данных профиля:', error);
            return html;
        }
    }

    showCachedModule(moduleId) {
        const cache = this.moduleCache.get(moduleId);
        if (cache) {
            const cacheAge = Date.now() - cache.timestamp;
            logInfo(`📤 Показ кэшированного модуля: ${moduleId} (возраст: ${Math.round(cacheAge/1000)}сек)`);
            this.renderPartial(moduleId, cache.html);
        } else {
            throw new Error(`Кэш для модуля ${moduleId} не найден`);
        }
    }

    renderPartial(moduleId, html) {
        this.hideCurrentModule();
        
        const modulesContainer = document.getElementById('modules-container');
        if (modulesContainer) {
            modulesContainer.innerHTML = html;

            // Автоматически инициализируем модули при загрузке
            setTimeout(() => {
                if (moduleId === 'edit-security') {
                    console.log('🔄 Автоматическая инициализация модуля безопасности');
                    if (typeof window.initializeSecurityHandlers === 'function') {
                        window.initializeSecurityHandlers();
                    }
                    if (typeof window.loadSecurityData === 'function') {
                        window.loadSecurityData();
                    }
                }
            }, 100);

            // Инициализируем обработчики событий для загруженного контента
            this.initializePartialEventHandlers(modulesContainer);
        }
    }

    initializePartialEventHandlers(container) {
        // Обработчики для кнопок внутри частичных страниц
        const actionButtons = container.querySelectorAll('[data-action]');
        actionButtons.forEach(button => {
            // Удаляем старые обработчики и добавляем новые
            button.replaceWith(button.cloneNode(true));
        });

        // Добавляем новые обработчики для action кнопок
        const newActionButtons = container.querySelectorAll('[data-action]');
        newActionButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const action = this.dataset.action;

                // Используем глобальный handleAction или fallback из profile-edit.js
                if (typeof window.handleAction !== 'undefined') {
                    window.handleAction(action, this, e);
                } else {
                    console.error('handleAction not found!');
                }
            });
        });

        // Обработчики для карточек с data-content
        const contentCards = container.querySelectorAll('.quick-action-card[data-content]');
        contentCards.forEach(card => {
            card.addEventListener('click', function(e) {
                e.preventDefault();
                const moduleId = this.dataset.content;
                if (moduleId && window.contentManager) {
                    window.contentManager.showModule(moduleId);
                }
            });
        });

        // Обработчики для кнопок с data-content
        const contentButtons = container.querySelectorAll('[data-content]:not(.quick-action-card)');
        contentButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const moduleId = this.dataset.content;
                if (moduleId && window.contentManager) {
                    window.contentManager.showModule(moduleId);
                }
            });
        });

        // ИНИЦИАЛИЗАЦИЯ ТИКЕТ СИСТЕМЫ ПОСЛЕ ЗАГРУЗКИ
        setTimeout(() => {
            console.log('🔄 Автоматическая инициализация тикет системы...');
            if (this.currentModule === 'user-tickets') {
                initializeUserTickets();
            } else if (this.currentModule === 'admin-tickets') {
                initializeAdminTickets();
            }
        }, 100);

        // ИНИЦИАЛИЗАЦИЯ АДМИНСКОЙ СТРАНИЦЫ ТИКЕТА
        setTimeout(() => {
            console.log('🔄 Проверка инициализации админской страницы тикета...');
            if (this.currentModule === 'admin-ticket-request') {
                console.log('🎯 Инициализация админской страницы тикета...');
                if (typeof initializeAdminTicketPage === 'function') {
                    initializeAdminTicketPage();
                } else {
                    console.error('❌ initializeAdminTicketPage не найдена');
                }
            }
        }, 100);

        logInfo(`✅ Обработчики событий инициализированы (${newActionButtons.length} кнопок, ${contentCards.length} карточек)`);
    }

    hideCurrentModule() {
        // Скрываем дашборд
        const dashboard = document.getElementById('dashboard-content');
        if (dashboard) {
            dashboard.style.display = 'none';
        }
        
        // Очищаем контейнер модулей
        const modulesContainer = document.getElementById('modules-container');
        if (modulesContainer) {
            modulesContainer.innerHTML = '';
        }
    }

    showLoading(moduleId) {
        this.hideCurrentModule();
        
        const modulesContainer = document.getElementById('modules-container');
        if (modulesContainer) {
            modulesContainer.innerHTML = `
                <div class="module-loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Загрузка ${this.modules.get(moduleId)?.title || moduleId}...</p>
                </div>
            `;
        }
    }

    async showDashboard() {
        logInfo('🔄 Показ дашборда');
        
        this.hideCurrentModule();
        
        // Показываем дашборд
        const dashboard = document.getElementById('dashboard-content');
        if (dashboard) {
            dashboard.style.display = 'block';
        }
    }

    updateUI(moduleId) {
        const module = this.modules.get(moduleId);
        if (module) {
            // Обновляем заголовок
            const titleElement = document.getElementById('contentTitle');
            if (titleElement) {
                titleElement.textContent = module.title;
            }
            
            // Обновляем хлебные крошки
            const breadcrumbElement = document.getElementById('breadcrumb');
            if (breadcrumbElement) {
                breadcrumbElement.innerHTML = module.breadcrumb
                    .map((item, index) => 
                        index === module.breadcrumb.length - 1 
                            ? `<span class="active">${item}</span>`
                            : `<span>${item}</span>`
                    )
                    .join(' / ');
            }
        }
    }

    updateActiveNav(moduleId) {
        // Убираем активный класс со всех пунктов
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        // Добавляем активный класс к выбранному пункту
        const activeLink = document.querySelector(`[data-content="${moduleId}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }
    }

    showError(moduleId, error) {
        const modulesContainer = document.getElementById('modules-container');
        if (modulesContainer) {
            modulesContainer.innerHTML = `
                <div class="module-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Ошибка загрузки</h3>
                    <p>Не удалось загрузить модуль "${moduleId}"</p>
                    <p><small>${error.message}</small></p>
                    <button class="btn-retry" onclick="contentManager.reloadModule('${moduleId}')">
                        <i class="fas fa-redo"></i>
                        Повторить попытку
                    </button>
                </div>
            `;
        }
    }

    // Метод для принудительной перезагрузки модуля
    async reloadModule(moduleId) {
        logInfo(`🔄 Принудительная перезагрузка модуля: ${moduleId}`);
        this.moduleCache.delete(moduleId);
        await this.showModule(moduleId);
    }
}

// Фоновое обновление профиля каждые 2 минуты
setInterval(() => {
    contentManager.moduleCache.delete('profile');
}, 120000);

// Создаем экземпляр менеджера контента
const contentManager = new ContentManager();

// Инициализация обработчиков событий
function initializeEventHandlers() {
    logInfo('Инициализация обработчиков событий...');
    
    // Обработчики для навигации по модулям
    const contentLinks = document.querySelectorAll('[data-content]');
    contentLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const moduleId = this.dataset.content;
            contentManager.showModule(moduleId);
            
            // Закрываем сайдбар на мобильных
            if (window.innerWidth <= 1024) {
                document.getElementById('sidebar').classList.remove('active');
            }
        });
    });
    
    // Обработчики для мобильного меню
    const mobileMenuItems = document.querySelectorAll('.mobile-menu-item[data-content]');
    mobileMenuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const moduleId = this.dataset.content;
            contentManager.showModule(moduleId);
            document.getElementById('sidebar').classList.remove('active');
        });
    });
    
    // Обработчики для кнопок действий
    const actionButtons = document.querySelectorAll('[data-action]');
    actionButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const action = this.dataset.action;
            handleAction(action, this, e);
        });
    });
    
    // Обработчик бургер меню
    const burgerMenu = document.getElementById('burgerMenu');
    const sidebar = document.getElementById('sidebar');
    
    if (burgerMenu && sidebar) {
        burgerMenu.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
    }
    
    // Закрытие сайдбара при клике вне его на мобильных
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 1024 && sidebar && sidebar.classList.contains('active')) {
            if (!sidebar.contains(e.target) && !burgerMenu.contains(e.target)) {
                sidebar.classList.remove('active');
            }
        }
    });
    
    // Обработчик выпадающего меню пользователя
    const userToggle = document.querySelector('.user-toggle');
    const dropdownMenu = document.querySelector('.dropdown-menu');
    
    if (userToggle && dropdownMenu) {
        userToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdownMenu.classList.toggle('show');
        });
        
        // Закрытие меню при клике вне его
        document.addEventListener('click', function() {
            dropdownMenu.classList.remove('show');
        });
    }
}

// Добавьте эту функцию ПЕРЕД функцией handleAction
function createNewTicket() {
    logInfo('Открытие формы создания тикета...');
    openCreateTicketModal();
}

// Функции для работы с модальным окном создания тикета
function openCreateTicketModal() {
    const modal = document.getElementById('create-ticket-modal');
    if (modal) {
        modal.style.display = 'flex';
        // Сброс формы
        document.getElementById('create-ticket-form').reset();
        document.getElementById('ticket-subject').focus();
    } else {
        logError('Модальное окно создания тикета не найдено');
        // Fallback: открываем страницу тикетов
        window.open('/tickets', '_blank');
    }
}

function closeCreateTicketModal() {
    const modal = document.getElementById('create-ticket-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Функция отправки формы тикета
async function submitTicketForm(event) {
    event.preventDefault();
    event.stopPropagation(); // Добавляем эту строку!

    console.log('Начало отправки формы тикета...');
    
    const form = event.target;
    const formData = new FormData(form);
    
    const subject = formData.get('subject');
    const description = formData.get('description');
    const priority = 'Medium';
    
    console.log('Данные формы:', { subject, description, priority });
    
    // Валидация
    if (!subject || !description) {
        showNotification('Пожалуйста, заполните тему и описание обращения', 'error');
        return;
    }
    
    if (subject.length < 5) {
        showNotification('Тема обращения должна содержать минимум 5 символов', 'error');
        return;
    }
    
    if (description.length < 10) {
        showNotification('Описание проблемы должно содержать минимум 10 символов', 'error');
        return;
    }
    
    try {
        // Показываем индикатор загрузки
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Отправка...';
        submitBtn.disabled = true;
        
        console.log('Отправка запроса на сервер...');
        

        const response = await fetch('/tickets/api/tickets', {
            method: 'POST',
            headers: {
                'accept': 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                subject: subject,
                description: description,
                priority: priority // Всегда "Medium" для новых обращений
            }),
            credentials: 'include'
        });
        
        console.log('Ответ сервера:', response.status, response.statusText);

        if (response.ok) {
            const result = await response.json();
            console.log('Тикет создан:', result);
            showNotification('Обращение успешно создано!', 'success');
            closeCreateTicketModal();
            
            // Обновляем список тикетов
            if (typeof loadUserTickets === 'function') {
                console.log('Обновление списка тикетов...');
                loadUserTickets();
            }
        } else {
            // Получаем детальную информацию об ошибке
            let errorMessage = 'Ошибка при создании обращения';
            try {
                const errorText = await response.text();
                console.error('Полный текст ответа:', errorText);
                
                let errorData;
                try {
                    errorData = JSON.parse(errorText);
                } catch {
                    errorData = { detail: errorText };
                }
                
                console.error('Детали ошибки:', errorData);
                
                if (errorData.detail) {
                    if (Array.isArray(errorData.detail)) {
                        errorMessage = errorData.detail.map(err => 
                            `${err.loc ? err.loc.join('.') + ': ' : ''}${err.msg}`
                        ).join(', ');
                    } else {
                        errorMessage = errorData.detail;
                    }
                }
            } catch (parseError) {
                console.error('Ошибка парсинга ответа:', parseError);
                errorMessage = `HTTP error! status: ${response.status}`;
            }
            throw new Error(errorMessage);
        }
        
    } catch (error) {
        console.error('Error creating ticket:', error);
        showNotification('Ошибка при создании обращения: ' + error.message, 'error');
    } finally {
        // Восстанавливаем кнопку
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Отправить обращение';
            submitBtn.disabled = false;
        }
    }
    
    return false;
}

// Обработчик действий
function handleAction(action, element, event = null) {
    logInfo(`Обработка действия: ${action}`, element);
    
    // Предотвращаем стандартное поведение если есть event
    if (event && event.preventDefault) {
        event.preventDefault();
    }
    
    // ОТЛАДКА: Проверим доступность функций
    if (action.startsWith('save-') || action.startsWith('change-') || action.includes('ip')) {
        console.log(`🔍 Проверка функции для действия ${action}:`, typeof window[action]);
    }
    
    switch(action) {
        case 'topup':
            topUpBalance();
            break;
        case 'logout':
            logoutUser();
            break;
        case 'create-project':
            createNewProject();
            break;
        case 'create-vps':
            navigateToService('vps');
            break;
        case 'create-docker':
            navigateToService('docker');
            break;
        case 'create-n8n':
            navigateToService('n8n');
            break;
        case 'support':
            window.location.href = '/ticket';
            break;
        case 'start-service':
        case 'stop-service':
            const serviceId = element.dataset.serviceId;
            if (serviceId) {
                const apiAction = action.replace('-service', '');
                manageService(apiAction, serviceId);
            }
            break;
            
        // ДЕЙСТВИЯ ДЛЯ ПРОФИЛЯ
        case 'save-basic-profile':
            if (typeof window.updateBasicProfile === 'function') {
                console.log('✅ Вызываем updateBasicProfile');
                window.updateBasicProfile(element);
            } else {
                console.error('❌ updateBasicProfile не найдена! Доступные глобальные функции:', 
                    Object.keys(window).filter(key => typeof window[key] === 'function' && key.includes('Basic')));
                showNotification('Ошибка: функция обновления профиля не доступна. Перезагрузите страницу.', 'error');
            }
            break;
            
        case 'change-password':
            if (typeof window.changePassword === 'function') {
                window.changePassword(element);
            } else {
                console.error('changePassword не найдена');
                showNotification('Ошибка: функция смены пароля не доступна', 'error');
            }
            break;
            
        case 'check-ip':
            if (typeof window.checkCurrentIP === 'function') {
                window.checkCurrentIP();
            } else {
                console.log('checkCurrentIP не найдена, используем локальную');
                checkCurrentIP();
            }
            break;
            
        case 'add-current-ip':
            if (typeof window.addCurrentIP === 'function') {
                console.log('✅ Вызываем addCurrentIP из profile-edit.js');
                window.addCurrentIP();
            } else {
                console.error('❌ addCurrentIP не найдена в profile-edit.js');
                showNotification('Ошибка: функция добавления IP не доступна', 'error');
            }
            break;
            
        case 'open-add-ip-modal':
            if (typeof window.openAddIPModal === 'function') {
                window.openAddIPModal();
            }
            break;
            
        case 'close-add-ip-modal':
            if (typeof window.closeAddIPModal === 'function') {
                window.closeAddIPModal();
            }
            break;
            
        case 'add-new-ip':
            if (typeof window.addNewIP === 'function') {
                window.addNewIP(element);
            }
            break;
            
        case 'remove-ip':
            const ipAddress = element.dataset.ip;
            if (typeof window.removeIP === 'function') {
                window.removeIP(ipAddress);
            }
            break;
        
        case 'create-ticket':
            createNewTicket(); // Теперь открывает модальное окно
            break;

        case 'close-create-ticket-modal':
            closeCreateTicketModal();
            break;

        case 'apply-admin-filters':
            if (typeof loadAdminTickets === 'function') {
                loadAdminTickets();
            }
            break;

        case 'reset-admin-filters':
           if (typeof loadAdminTickets === 'function') {
               // Сброс уже выполняется в обработчике, просто вызываем загрузку
               loadAdminTickets();
           }
           break;
            
        default:
            logWarning(`Неизвестное действие: ${action}`);
    }
}

// Функции авторизации
async function regFunction(event) {
    logInfo('Обработка регистрации...');
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    logInfo('Данные регистрации:', data);

    // Клиентская проверка совпадения паролей
    if (data.user_pass !== data.user_pass_check) {
        showNotification('Пароли не совпадают!', 'error');
        return;
    }

    try {
        logInfo('Отправка запроса регистрации...');
        const response = await fetch('/users/register/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data),
            credentials: 'include'
        });

        logInfo('Ответ регистрации:', response.status);

        if (!response.ok) {
            const errorData = await response.json();
            logError('Ошибка регистрации:', errorData);
            displayErrors(errorData);
            return;
        }

        const result = await response.json();
        logSuccess('Успешная регистрация:', result);

        if (result.message) {
            showNotification(result.message, 'success');
            setTimeout(() => {
                showTab('login');
            }, 2000);
        } else {
            showNotification(result.message || 'Неизвестная ошибка', 'error');
        }
    } catch (error) {
        logError('Ошибка сети при регистрации:', error);
        showNotification('Произошла ошибка при регистрации. Пожалуйста, попробуйте снова.', 'error');
    }
}

async function loginFunction(event) {
    logInfo('Обработка авторизации...');
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    logInfo('Данные авторизации:', { user_email: data.user_email });

    try {
        logInfo('Отправка запроса авторизации...');
        const response = await fetch('/users/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data),
            credentials: 'include'
        });

        logInfo('Ответ авторизации:', response.status, response.statusText);

        // Получаем текст ответа для отладки
        const responseText = await response.text();
        logInfo('Текст ответа:', responseText);

        // Пытаемся распарсить JSON
        let result;
        try {
            result = JSON.parse(responseText);
        } catch (parseError) {
            logError('Ошибка парсинга JSON:', parseError);
            showNotification('Неверный формат ответа от сервера', 'error');
            return;
        }

        if (!response.ok) {
            logError('Ошибка авторизации:', result);
            displayErrors(result);
            return;
        }

        logSuccess('Успешная авторизация:', result);

        // Проверяем успешность разными способами
        if (result.ok === true || result.message || result.user_id) {
            showNotification(result.message || 'Авторизация успешна!', 'success');
            logSuccess('Выполняем редирект на:', result.redirect_url || '/lk/plist');
            
            setTimeout(() => {
                window.location.href = result.redirect_url || '/lk/plist';
            }, 1000);
        } else {
            logWarning('Непонятный ответ от сервера:', result);
            showNotification(result.message || 'Неизвестная ошибка', 'error');
        }
    } catch (error) {
        logError('Ошибка сети при авторизации:', error);
        showNotification('Произошла ошибка при входе. Пожалуйста, попробуйте снова.', 'error');
    }
}

// Функция для отображения ошибок
function displayErrors(errorData) {
    let message = 'Произошла ошибка';

    if (errorData && errorData.detail) {
        if (Array.isArray(errorData.detail)) {
            message = errorData.detail.map(error => {
                if (error.type === 'string_too_short') {
                    return `Поле "${error.loc[1]}" должно содержать минимум ${error.ctx.min_length} символов.`;
                }
                return error.msg || 'Произошла ошибка';
            }).join('\n');
        } else {
            message = errorData.detail || 'Произошла ошибка';
        }
    }

    showNotification(message, 'error');
}

// Функции для работы с редактированием профиля
let activeEditTab = 'basic-tab';

// function checkCurrentIP() {
//     fetch('/users/ip-restrictions/check')
//         .then(response => response.json())
//         .then(data => {
//             document.getElementById('current-ip').textContent = data.ip_address;
//             const statusElement = document.getElementById('ip-access-status');
//             if (data.is_allowed) {
//                 statusElement.textContent = '✅ Разрешен';
//                 statusElement.className = 'text-success';
//             } else {
//                 statusElement.textContent = '❌ Заблокирован';
//                 statusElement.className = 'text-danger';
//             }
//         })
//         .catch(error => {
//             console.error('Error checking IP:', error);
//             document.getElementById('current-ip').textContent = 'Ошибка';
//             document.getElementById('ip-access-status').textContent = '❌ Ошибка проверки';
//             document.getElementById('ip-access-status').className = 'text-danger';
//         });
// }

// Функции для работы с IP-адресами
function checkCurrentIP() {
    fetch('/users/ip-restrictions/check')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const currentIpElement = document.getElementById('current-ip');
            const securityCurrentIpElement = document.getElementById('security-current-ip');
            
            if (currentIpElement) {
                currentIpElement.textContent = data.ip_address;
            }
            if (securityCurrentIpElement) {
                securityCurrentIpElement.textContent = data.ip_address;
            }
            
            const statusElement = document.getElementById('ip-access-status');
            if (statusElement) {
                if (data.is_allowed) {
                    statusElement.textContent = '✅ Разрешен';
                    statusElement.className = 'text-success';
                } else {
                    statusElement.textContent = '❌ Заблокирован';
                    statusElement.className = 'text-danger';
                }
            }
        })
        .catch(error => {
            console.error('Error checking IP:', error);
            const currentIpElement = document.getElementById('current-ip');
            const securityCurrentIpElement = document.getElementById('security-current-ip');
            
            if (currentIpElement) currentIpElement.textContent = 'Ошибка';
            if (securityCurrentIpElement) securityCurrentIpElement.textContent = 'Ошибка';
            
            const statusElement = document.getElementById('ip-access-status');
            if (statusElement) {
                statusElement.textContent = '❌ Ошибка проверки';
                statusElement.className = 'text-danger';
            }
        });
}

// // Функции для работы с профилем
// async function updateBasicProfile(formElement) {
//     // Перенаправляем на функцию из profile-edit.js
//     if (typeof window.updateBasicProfile !== 'undefined') {
//         window.updateBasicProfile(formElement);
//     } else {
//         console.error('updateBasicProfile not found in profile-edit.js');
//         showNotification('Ошибка: функция обновления профиля не найдена', 'error');
//     }
// }

// async function changePassword(formElement) {
//     // Перенаправляем на функцию из profile-edit.js
//     if (typeof window.changePassword !== 'undefined') {
//         window.changePassword(formElement);
//     } else {
//         console.error('changePassword not found in profile-edit.js');
//         showNotification('Ошибка: функция смены пароля не найдена', 'error');
//     }
// }

// Делаем функции глобально доступными
window.initializeAdminTicketPage = initializeAdminTicketPage;
window.loadAdminTicketDetail = loadAdminTicketDetail;
window.handleAdminReply = handleAdminReply;
window.previewAdminMessage = previewAdminMessage;
window.updateAdminTicket = updateAdminTicket;
window.closeAdminTicket = closeAdminTicket;
window.togglePinTicket = togglePinTicket; // Если еще не глобальная

// Глобальные методы для отладки
window.debugContentManager = {
    showState: function() {
        console.log('=== ContentManager State ===');
        console.log('Current module:', window.contentManager.currentModule);
        console.log('Cached modules:', Array.from(window.contentManager.moduleCache.keys()));
        
        Array.from(window.contentManager.moduleCache.entries()).forEach(([moduleId, cache]) => {
            const age = Math.round((Date.now() - cache.timestamp) / 1000);
            console.log(`- ${moduleId}: ${age}сек назад`);
        });
    },
    
    reloadProfile: function() {
        window.contentManager.reloadModule('profile');
    },
    
    clearCache: function() {
        window.contentManager.moduleCache.clear();
        console.log('✅ Кэш очищен');
    },
    
    // Новые методы для работы с датами
    testDateCalculation: function(registrationDate, lastLoginDate) {
        console.log('=== Тест расчета дат ===');
        console.log('Дата регистрации:', registrationDate);
        console.log('Дней с нами:', calculateDaysWithUs(registrationDate));
        console.log('Последний вход:', lastLoginDate);
        console.log('Форматированный вход:', formatLastLogin(lastLoginDate));
    },
    
    // Метод для тестирования текущего профиля
    testCurrentProfile: function() {
        const daysElement = document.querySelector('#days-with-us');
        const loginElement = document.querySelector('#last-login-time');
        
        if (daysElement) {
            console.log('Элемент дней с нами:', daysElement);
            console.log('Data атрибут:', daysElement.dataset.registrationDate);
        }
        
        if (loginElement) {
            console.log('Элемент последнего входа:', loginElement);
            console.log('Data атрибут:', loginElement.dataset.lastLogin);
        }
    },

    // Новые методы для профиля
    testProfileActions: function() {
        console.log('=== Тест действий профиля ===');
        console.log('Функция openEditProfile:', typeof openEditProfile);
        console.log('Функция closeEditProfile:', typeof closeEditProfile);
        console.log('Функция checkCurrentIP:', typeof checkCurrentIP);
        console.log('Активная вкладка:', activeEditTab);
    },
    
    openTestModal: function(tab = 'basic-tab') {
        openEditProfile(tab);
    }
};