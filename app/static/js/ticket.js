import { marked } from 'marked'; // Import the marked library

const LS_KEY = 'hostgenius_tickets';
const appContainer = document.getElementById('app-container');

// --- Utility Constants & Functions for Attachments/Links ---
const MAX_FILE_SIZE = 1048576; // 1MB

// Configure marked globally for message formatting
marked.setOptions({
    breaks: true, // Single newline becomes <br> (GFM line breaks)
    gfm: true,
});

function validateFile(fileInput) {
    if (fileInput.files.length === 0) return { isValid: true, metadata: null };

    const file = fileInput.files[0];
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg'];
    
    // Normalize file type check (some browsers report image/pjpeg for jpg)
    const fileType = file.type;

    if (file.size > MAX_FILE_SIZE) {
        return { isValid: false, message: 'Файл слишком большой. Максимальный размер 1MB.' };
    }
    
    if (!allowedTypes.includes(fileType) && !(fileType === 'image/pjpeg' && allowedTypes.includes('image/jpeg'))) {
        return { isValid: false, message: 'Неподдерживаемый тип файла. Допустимы только PNG и JPG.' };
    }
    
    const metadata = {
        name: file.name,
        size: file.size,
        type: file.type,
    };

    return { isValid: true, metadata };
}

function formatMessageText(text) {
    if (!text) return '';
    
    let formattedText = marked.parse(text);

    // marked.parse often returns HTML wrapped in <p></p>. In a messaging context, 
    // this causes spacing issues. We try to strip them if they wrap the entire content.
    formattedText = formattedText.trim();
    // Check if the content is exactly one paragraph block
    if (formattedText.startsWith('<p>') && formattedText.endsWith('</p>')) {
        // Remove surrounding <p>...</p> tags
        formattedText = formattedText.substring(3, formattedText.length - 4).trim();
    }
    
    return formattedText;
}

function renderAttachment(attachment) {
    if (!attachment) return '';
    
    const sizeKB = (attachment.size / 1024).toFixed(1);
    
    return `
        <div style="margin-top: 8px; padding: 5px; border: 1px dashed #999; border-radius: 4px; font-size: 0.9em; background-color: #f0f0f0;">
            📎 <strong>Прикрепленный файл:</strong> ${attachment.name} (${sizeKB} KB)
            <br>
            <span style="color: #666;">(Файл не хранится в демо-системе. Тип: ${attachment.type})</span>
        </div>
    `;
}

// NEW: Utility function to check if the screen is considered mobile based on CSS breakpoint
function isMobileView() {
    // Check width used in CSS media query: @media (max-width: 600px)
    return window.matchMedia('(max-width: 600px)').matches;
}


// --- Utility Functions ---

function getTickets() {
    try {
        const ticketsJson = localStorage.getItem(LS_KEY);
        return ticketsJson ? JSON.parse(ticketsJson) : [];
    } catch (e) {
        console.error("Error loading tickets from localStorage:", e);
        return [];
    }
}

function saveTickets(tickets) {
    try {
        localStorage.setItem(LS_KEY, JSON.stringify(tickets));
    } catch (e) {
        console.error("Error saving tickets to localStorage:", e);
    }
}

function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substring(2, 9);
}

function formatDate(timestamp) {
    return new Date(timestamp).toLocaleString('ru-RU', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

const TicketSystem = (() => {
    let tickets = [];
    let currentView = 'user-portal';
    let currentTicketId = null;
    let currentUser = localStorage.getItem('current_user_email') || 'user@example.com'; 

    // Paginaton/Admin state
    let ticketsPerPage = 25; 
    let currentPage = 1; 
    const MAX_TICKETS = 500; // Hard limit for display/pagination scope

    const PRIORITY_OPTIONS = ['Low', 'Medium', 'High', 'Urgent'];
    const STATUS_OPTIONS = ['Open', 'In Progress', 'Awaiting User Response', 'Closed'];

    // NEW: Define user portal specific sorting order
    const USER_STATUS_SORT_ORDER = {
        'Awaiting User Response': 1,
        'In Progress': 2,
        'Open': 3,
        'Closed': 4
    };

    // --- State Management / Routing ---

    function initialize() {
        tickets = getTickets();
        
        // If no tickets, add some sample data for demonstration
        if (tickets.length === 0) {
            tickets = [
                {
                    id: generateId(),
                    user: 'ivanov@hosting.com',
                    subject: 'Проблема с подключением по SSH',
                    description: 'Не удается подключиться к серверу по SSH. Ошибка "Connection refused". Порт 22.',
                    status: 'Open',
                    priority: 'High',
                    createdAt: Date.now() - 3600000,
                    updatedAt: Date.now(),
                    messages: [
                        { sender: 'user', text: 'Не удается подключиться к серверу по SSH. Ошибка "Connection refused". Порт 22.', timestamp: Date.now() - 3600000, attachment: null }
                    ],
                    isPinned: true // Sample pinned ticket
                },
                {
                    id: generateId(),
                    user: 'petrov@domain.ru',
                    subject: 'Вопрос по продлению домена',
                    description: 'Когда истекает срок регистрации домена mydomain.ru и как его продлить?',
                    status: 'Closed',
                    priority: 'Low',
                    createdAt: Date.now() - 86400000 * 5,
                    updatedAt: Date.now() - 86400000 * 4,
                    messages: [
                        { sender: 'user', text: 'Вопрос по продлению домена.', timestamp: Date.now() - 86400000 * 5, attachment: null },
                        { sender: 'staff', text: 'Здравствуйте! Ваш домен истекает через 30 дней. Вы можете продлить его через личный кабинет.', timestamp: Date.now() - 86400000 * 4, attachment: null }
                    ],
                    isPinned: false
                }
            ];
            saveTickets(tickets);
        }
        
        // Ensure all existing tickets have the isPinned property initialized
        tickets = tickets.map(t => ({
            ...t,
            isPinned: t.isPinned ?? false 
        }));
        
        handleRoute();
        
        // Setup navigation listeners
        document.getElementById('main-nav').addEventListener('click', (e) => {
            if (e.target.tagName === 'BUTTON') {
                const view = e.target.getAttribute('data-view');
                if (view === 'admin-panel') {
                    if (prompt("Введите пароль администратора (pass):") === 'pass') {
                        navigateTo('admin-panel');
                    } else {
                        alert("Неверный пароль.");
                    }
                } else {
                    navigateTo('user-portal');
                }
            }
        });

        window.addEventListener('hashchange', handleRoute);
    }
    
    function navigateTo(view, ticketId = null) {
        
        // If navigating to user portal, try to preserve the currently selected ticket if present
        // This is crucial for the split view refresh upon sending a reply
        if (view === 'user-portal' && currentView === 'user-portal' && ticketId === null) {
             // Keep existing currentTicketId
        } else {
            currentTicketId = ticketId;
        }

        currentView = view;
        
        // Reset pagination when navigating away from or into admin panel main view
        if (view !== 'admin-panel') {
            currentPage = 1;
            ticketsPerPage = 25;
        }

        // Use hash routing
        if (view.endsWith('-detail') && ticketId) {
            const context = view.startsWith('admin') ? 'admin' : 'user';
            window.location.hash = `ticket/${ticketId}/${context}`;
        } else {
            window.location.hash = view;
        }
        render();
    }
    
    function handleRoute() {
        const hash = window.location.hash.slice(1);
        if (hash.startsWith('ticket/')) {
            const parts = hash.split('/');
            if (parts[1]) {
                currentTicketId = parts[1];
                const context = parts[2]; 
                
                if (context === 'admin') {
                    currentView = 'admin-detail';
                } else if (context === 'user') {
                    // Force user detail links to load the main portal view, where selection logic takes over
                    currentView = 'user-portal';
                } else {
                    currentView = 'user-portal';
                }
            }
        } else if (hash === 'new-ticket') {
             currentView = 'new-ticket';
        } else if (hash === 'admin-panel') {
            currentView = 'admin-panel';
        } else {
            currentView = 'user-portal';
        }
        render();
    }

    // --- Rendering Functions ---
    
    function setPaginationParams(perPage, page) {
        ticketsPerPage = perPage;
        currentPage = page;
        render();
    }

    function render() {
        appContainer.innerHTML = '';
        switch (currentView) {
            case 'new-ticket':
                renderNewTicketForm();
                break;
            case 'user-detail':
                renderTicketDetail(currentTicketId, false);
                break;
            case 'admin-detail':
                renderTicketDetail(currentTicketId, true);
                break;
            case 'admin-panel':
                renderAdminPanel();
                break;
            case 'user-portal':
            default:
                renderUserPortal();
                break;
        }
    }

    // --- Components ---

    function createTicketItemHTML(ticket, isAdmin = false) {
        const statusTag = `<span class="status-tag status-${ticket.status.replace(/\s/g, '')}">${ticket.status}</span>`;
        const userDisplay = isAdmin ? ` (${ticket.user})` : '';
        
        const pinControl = isAdmin && ticket.status !== 'Closed' ? 
            `<button class="pin-toggle-btn" data-id="${ticket.id}" title="${ticket.isPinned ? 'Открепить' : 'Закрепить'}" type="button">
                ${ticket.isPinned ? '📌' : '📍'}
            </button>` : '';

        return `
            <li class="ticket-item card ${ticket.isPinned ? 'pinned-ticket' : ''}" data-id="${ticket.id}">
                <div class="ticket-main-content">
                    <strong>#${ticket.id.substring(0, 8).toUpperCase()}</strong>: ${ticket.subject} ${userDisplay}
                    <div style="font-size: 0.8em; color: #777; margin-top: 5px;">
                        Приоритет: ${ticket.priority} | Создано: ${formatDate(ticket.createdAt)}
                    </div>
                </div>
                <div class="ticket-actions">
                    ${statusTag}
                    ${pinControl}
                </div>
            </li>
        `;
    }

    function renderTicketList(filteredTickets, title, isAdmin = false, clickHandler = null) {
        const listElement = document.createElement('div');
        
        if (filteredTickets.length === 0) {
            let message = 'У вас пока нет обращений.';
            // Customize message if it's a paginated slice but the total pool is known
            if (title.includes('Стр.')) {
                message = 'На текущей странице нет обращений данного типа.';
            }

            const listHtml = `<div class="card"><h2>${title}</h2><p>${message}</p></div>`;
            listElement.innerHTML = listHtml;
            return listElement;
        }

        const listItems = filteredTickets.map(t => createTicketItemHTML(t, isAdmin)).join('');

        const listHtml = `<div class="card">
            <h2>${title}</h2>
            <ul class="ticket-list">
                ${listItems}
            </ul>
        </div>`;
        
        listElement.innerHTML = listHtml;
        
        listElement.querySelectorAll('.ticket-item').forEach(item => {
            item.addEventListener('click', (e) => {
                // Prevent navigation if clicking the pin button itself
                if (e.target.closest('.pin-toggle-btn')) {
                    return; 
                }
                const id = item.getAttribute('data-id');
                
                // Use custom handler if provided (for user portal split view)
                if (clickHandler) {
                    clickHandler(id);
                } else {
                    // Original behavior for Admin panel or dedicated detail view
                    const viewContext = isAdmin ? 'admin-detail' : 'user-detail';
                    navigateTo(viewContext, id);
                }
            });
        });

        // Add event listeners for pinning (Admin only list context)
        if (isAdmin) {
            listElement.querySelectorAll('.pin-toggle-btn').forEach(button => {
                button.addEventListener('click', (e) => {
                    const id = button.getAttribute('data-id');
                    toggleTicketPin(id);
                    render(); // Re-render the admin panel to update lists
                });
            });
        }

        return listElement;
    }
    
    // --- Views ---

    function renderUserPortal() {
        const userEmailInput = `<div class="card" style="margin-bottom: 30px;">
            <h3>Ваш E-mail для просмотра заявок</h3>
            <input type="email" id="user-email-input" value="${currentUser}" placeholder="Введите ваш E-mail">
            <button id="set-user-email" style="margin-top: 10px;">Применить</button>
        </div>`;
        
        appContainer.innerHTML = userEmailInput;
        
        document.getElementById('set-user-email').addEventListener('click', () => {
            const email = document.getElementById('user-email-input').value.trim();
            if (email) {
                currentUser = email;
                localStorage.setItem('current_user_email', email);
                navigateTo('user-portal');
            } else {
                alert("Пожалуйста, введите ваш E-mail.");
            }
        });


        const header = `<div class="card">
            <h2>Портал Клиента</h2>
            <p>Добро пожаловать, ${currentUser}.</p>
            <button id="create-new-ticket">Создать новое обращение</button>
        </div>`;
        appContainer.insertAdjacentHTML('beforeend', header);
        
        document.getElementById('create-new-ticket').addEventListener('click', () => navigateTo('new-ticket'));
        
        const userTickets = tickets.filter(t => t.user === currentUser);
        
        // Apply sorting based on user requirements: Awaiting User Response, In Progress, Open, Closed
        userTickets.sort((a, b) => {
            const statusOrderA = USER_STATUS_SORT_ORDER[a.status] || 99;
            const statusOrderB = USER_STATUS_SORT_ORDER[b.status] || 99;

            if (statusOrderA !== statusOrderB) {
                return statusOrderA - statusOrderB;
            }
            
            // Secondary sort: By updated date, newest first
            return b.updatedAt - a.updatedAt;
        });
        
        // Mobile override: If a ticket is selected via hash on mobile, navigate immediately to the detail view.
        if (isMobileView() && currentTicketId && userTickets.some(t => t.id === currentTicketId)) {
            navigateTo('user-detail', currentTicketId);
            return;
        }

        // Setup Two Column Layout (New requirement)
        const portalLayout = document.createElement('div');
        portalLayout.className = 'two-column-portal';
        portalLayout.innerHTML = `
            <div id="portal-left-column" class="portal-left-column"></div>
            <div id="portal-right-column" class="portal-right-column">
                <div class="card ticket-history-panel" id="detail-placeholder">
                    <h2>История обращений</h2>
                    <p>Выберите обращение из списка слева, чтобы увидеть историю переписки.</p>
                </div>
            </div>
        `;
        appContainer.appendChild(portalLayout);

        const leftColumn = document.getElementById('portal-left-column');
        const rightColumn = document.getElementById('portal-right-column');
        
        // Define Ticket Click Handler for User Portal
        const handleTicketSelection = (id) => {
            currentTicketId = id; // Update state
            
            // NEW: If mobile, navigate to the dedicated full detail view
            if (isMobileView()) {
                navigateTo('user-detail', id);
                return;
            }

            // Highlight selected ticket (Desktop/Split View behavior)
            document.querySelectorAll('#portal-left-column .ticket-item').forEach(item => {
                item.classList.remove('selected');
                if (item.getAttribute('data-id') === id) {
                    item.classList.add('selected');
                }
            });
            
            // Update URL hash to reflect selection (allows link sharing/refresh)
            window.history.replaceState(null, null, `#ticket/${id}/user`);

            renderUserTicketHistory(id, rightColumn);
        };
        
        // Render Ticket List into Left Column
        const listElement = renderTicketList(userTickets, `Ваши обращения (${currentUser})`, false, handleTicketSelection);
        leftColumn.appendChild(listElement);

        // Automatically select the first ticket or previously selected one (from hash/state)
        let defaultSelectionId = userTickets.length > 0 ? userTickets[0].id : null;
        
        if (currentTicketId && userTickets.some(t => t.id === currentTicketId)) {
            defaultSelectionId = currentTicketId;
        } else {
            // Clear currentTicketId if the ticket is not relevant to the current user/list
            currentTicketId = null; 
        }

        if (defaultSelectionId && !isMobileView()) { // Only auto-select and render detail on desktop
            handleTicketSelection(defaultSelectionId);
        }
    }

    function renderNewTicketForm() {
        appContainer.innerHTML = `
            <div class="card">
                <h2>Создание нового обращения</h2>
                <form id="new-ticket-form">
                    <label for="email">Ваш E-mail (идентификатор):</label>
                    <input type="email" id="email" value="${currentUser}" required>

                    <label for="subject">Тема:</label>
                    <input type="text" id="subject" placeholder="Краткое описание проблемы" required>

                    <label for="priority">Приоритет:</label>
                    <select id="priority" required>
                        ${PRIORITY_OPTIONS.map(p => `<option value="${p}" ${p === 'Medium' ? 'selected' : ''}>${p}</option>`).join('')}
                    </select>

                    <label for="description">Полное описание проблемы:</label>
                    <textarea id="description" required></textarea>
                    
                    <label for="attachment" style="margin-top: 10px;">Прикрепить файл (PNG/JPG, до 1MB):</label>
                    <input type="file" id="attachment" accept="image/png, image/jpeg, image/jpg">


                    <button type="submit">Отправить обращение</button>
                    <button type="button" id="cancel-ticket-creation" style="margin-left: 10px; background-color: #aaa; margin-top: 20px;">Отмена</button>
                </form>
            </div>
        `;
        
        document.getElementById('cancel-ticket-creation').addEventListener('click', () => navigateTo('user-portal'));

        document.getElementById('new-ticket-form').addEventListener('submit', handleNewTicketSubmit);
    }

    function handleNewTicketSubmit(e) {
        e.preventDefault();
        
        const email = document.getElementById('email').value.trim();
        const subject = document.getElementById('subject').value.trim();
        const priority = document.getElementById('priority').value;
        const description = document.getElementById('description').value.trim();
        const attachmentInput = document.getElementById('attachment'); // NEW

        const fileValidation = validateFile(attachmentInput); // NEW
        
        if (!fileValidation.isValid) {
            alert(fileValidation.message);
            return;
        }

        if (!email || !subject || (!description && !fileValidation.metadata)) { // Must have text OR attachment
            alert('Пожалуйста, заполните E-mail, тему и введите описание проблемы или прикрепите файл.');
            return;
        }

        const initialMessage = {
            sender: 'user', 
            text: description, 
            timestamp: Date.now(),
            attachment: fileValidation.metadata // Store metadata
        };
        
        const newTicket = {
            id: generateId(),
            user: email,
            subject: subject,
            description: description,
            status: 'Open',
            priority: priority,
            createdAt: Date.now(),
            updatedAt: Date.now(),
            messages: [initialMessage],
            isPinned: false // New ticket is not pinned by default
        };
        
        tickets.push(newTicket);
        saveTickets(tickets);
        
        // Update current user if different
        currentUser = email;
        localStorage.setItem('current_user_email', email);

        alert('Ваше обращение успешно создано!');
        navigateTo('user-detail', newTicket.id);
    }
    
    // NEW: Function to render ticket history specifically for the User Portal split view
    function renderUserTicketHistory(ticketId, containerElement) {
        const ticket = tickets.find(t => t.id === ticketId);
        
        if (!ticket || ticket.user !== currentUser) {
            containerElement.innerHTML = `<div class="card ticket-history-panel"><h2>Ошибка доступа</h2><p>Обращение не найдено или у вас нет прав.</p></div>`;
            return;
        }
        
        // Render history
        const messageHistoryHtml = ticket.messages.map(msg => {
            const formattedText = formatMessageText(msg.text);
            const attachmentHtml = renderAttachment(msg.attachment);
            
            return `
                <div class="message ${msg.sender}">
                    <div class="message-sender">${msg.sender === 'staff' ? 'Техподдержка' : (msg.sender === 'user' ? 'Вы' : msg.sender)}</div>
                    ${formattedText}
                    ${attachmentHtml}
                    <span class="message-timestamp">${formatDate(msg.timestamp)}</span>
                </div>
            `;
        }).join('');

        const historyHtml = `
            <div class="card ticket-history-panel">
                <h2>${ticket.subject}</h2>
                <p><strong>ID:</strong> #${ticket.id.substring(0, 8).toUpperCase()}</p>
                <p><strong>Приоритет:</strong> ${ticket.priority}</p>
                <p><strong>Статус:</strong> <span class="status-tag status-${ticket.status.replace(/\s/g, '')}">${ticket.status}</span></p>
                <p><strong>Последнее обновление:</strong> ${formatDate(ticket.updatedAt)}</p>

                <h3 style="margin-top: 20px;">История переписки</h3>
                <div class="message-history" id="message-history-${ticketId}">
                    ${messageHistoryHtml || '<p>Нет сообщений в истории.</p>'}
                </div>

                <h3>Добавить ответ</h3>
                ${ticket.status !== 'Closed' ? `
                    <form id="add-message-form-${ticketId}">
                        <label for="new-message-text-${ticketId}">Сообщение:</label>
                        <textarea id="new-message-text-${ticketId}" required></textarea>
                        
                        <label for="reply-attachment-${ticketId}" style="margin-top: 10px;">Прикрепить файл (PNG/JPG, до 1MB):</label>
                        <input type="file" id="reply-attachment-${ticketId}" accept="image/png, image/jpeg, image/jpg">
                        
                        <button type="submit">Отправить</button>
                    </form>
                ` : `<p>Это обращение закрыто. Вы не можете добавить новый ответ.</p>`}
            </div>
        `;
        
        containerElement.innerHTML = historyHtml;
        
        // Attach listener for new message form
        if (ticket.status !== 'Closed') {
            const form = document.getElementById(`add-message-form-${ticketId}`);
            if (form) {
                 form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    const textInput = document.getElementById(`new-message-text-${ticketId}`);
                    const text = textInput.value.trim();
                    const attachmentInput = document.getElementById(`reply-attachment-${ticketId}`);
                    
                    const fileValidation = validateFile(attachmentInput);
                    
                    if (!fileValidation.isValid) {
                        alert(fileValidation.message);
                        return;
                    }

                    if (!text && !fileValidation.metadata) {
                        alert("Пожалуйста, введите сообщение или прикрепите файл.");
                        return;
                    }
                    
                    // User is replying, status changes to Open if not closed
                    addMessageToTicket(ticketId, 'user', text, fileValidation.metadata); 
                    updateTicket(ticketId, { status: 'Open' }); // User reply moves status to Open
                    
                    textInput.value = '';
                    attachmentInput.value = ''; 
                    
                    // Re-render the User Portal to update both lists (if sorting changed) and the detail panel
                    navigateTo('user-portal'); 
                });
            }
        }
        
        // Scroll message history to bottom
        const historyDiv = document.getElementById(`message-history-${ticketId}`);
        if(historyDiv) {
            historyDiv.scrollTop = historyDiv.scrollHeight;
        }
    }

    function renderTicketDetail(ticketId, isAdmin) {
        const ticket = tickets.find(t => t.id === ticketId);
        if (!ticket) {
            appContainer.innerHTML = '<div class="card"><h2>Ошибка</h2><p>Обращение не найдено.</p></div>';
            return;
        }
        
        // Check authorization 
        if (!isAdmin && ticket.user !== currentUser) {
             appContainer.innerHTML = '<div class="card"><h2>Ошибка доступа</h2><p>У вас нет прав для просмотра этого обращения.</p></div>';
             return;
        }

        const messageHistoryHtml = ticket.messages.map(msg => {
            const formattedText = formatMessageText(msg.text);
            const attachmentHtml = renderAttachment(msg.attachment);
            
            return `
                <div class="message ${msg.sender}">
                    <div class="message-sender">${msg.sender === 'staff' ? 'Техподдержка' : (msg.sender === 'user' ? 'Вы' : msg.sender)}</div>
                    ${formattedText}
                    ${attachmentHtml}
                    <span class="message-timestamp">${formatDate(msg.timestamp)}</span>
                </div>
            `;
        }).join('');

        const adminControls = isAdmin ? `
            <div class="admin-controls card" style="margin-bottom: 20px;">
                <h3>Управление обращением</h3>
                <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                    <div>
                        <label for="status-select">Статус:</label>
                        <select id="status-select">
                            ${STATUS_OPTIONS.map(s => `<option value="${s}" ${s === ticket.status ? 'selected' : ''}>${s}</option>`).join('')}
                        </select>
                        <button id="update-status-btn">Обновить статус</button>
                    </div>
                    <div>
                        <label for="priority-select">Приоритет:</label>
                        <select id="priority-select">
                            ${PRIORITY_OPTIONS.map(p => `<option value="${p}" ${p === ticket.priority ? 'selected' : ''}>${p}</option>`).join('')}
                        </select>
                         <button id="update-priority-btn">Обновить приоритет</button>
                    </div>
                </div>
            </div>
        ` : '';

        appContainer.innerHTML = `
            <div class="card ticket-detail">
                <button id="back-to-list" style="margin-bottom: 15px; background-color: #666;">← Назад</button>
                <h2>Обращение #${ticket.id.substring(0, 8).toUpperCase()}: ${ticket.subject}</h2>
                <p><strong>Клиент:</strong> ${ticket.user}</p>
                <p><strong>Создано:</strong> ${formatDate(ticket.createdAt)}</p>
                <p><strong>Последнее обновление:</strong> ${formatDate(ticket.updatedAt)}</p>
                <p><strong>Приоритет:</strong> <span style="font-weight: bold; color: ${ticket.priority === 'Urgent' ? 'red' : 'inherit'};">${ticket.priority}</span></p>
                <p><strong>Статус:</strong> <span class="status-tag status-${ticket.status.replace(/\s/g, '')}">${ticket.status}</span></p>
                
                ${adminControls}

                <h3>История переписки</h3>
                <div class="message-history">
                    ${messageHistoryHtml || '<p>Нет сообщений в истории.</p>'}
                </div>

                <h3>Добавить ответ</h3>
                <form id="add-message-form">
                    <label for="new-message-text">Сообщение:</label>
                    <textarea id="new-message-text" required></textarea>
                    
                    <label for="reply-attachment" style="margin-top: 10px;">Прикрепить файл (PNG/JPG, до 1MB):</label>
                    <input type="file" id="reply-attachment" accept="image/png, image/jpeg, image/jpg">
                    
                    ${isAdmin ? '<label style="display: block; margin-top: 10px;"><input type="checkbox" id="reply-as-staff" checked> Ответить как Техподдержка</label>' : ''}
                    <button type="submit">Отправить</button>
                </form>
            </div>
        `;
        
        document.getElementById('back-to-list').addEventListener('click', () => navigateTo(isAdmin ? 'admin-panel' : 'user-portal'));

        // Handle Status/Priority updates (Admin only)
        if (isAdmin) {
            document.getElementById('update-status-btn').addEventListener('click', () => {
                const newStatus = document.getElementById('status-select').value;
                updateTicket(ticketId, { status: newStatus });
                
                // If status is set to Closed, navigate back to the admin list
                if (newStatus === 'Closed') {
                    navigateTo('admin-panel');
                } else {
                    navigateTo('admin-detail', ticketId);
                }
            });
            document.getElementById('update-priority-btn').addEventListener('click', () => {
                const newPriority = document.getElementById('priority-select').value;
                updateTicket(ticketId, { priority: newPriority });
                navigateTo('admin-detail', ticketId);
            });
        }
        
        document.getElementById('add-message-form').addEventListener('submit', (e) => {
            e.preventDefault();
            const textInput = document.getElementById('new-message-text');
            const text = textInput.value.trim();
            const attachmentInput = document.getElementById('reply-attachment');
            
            const fileValidation = validateFile(attachmentInput); // NEW
            
            if (!fileValidation.isValid) {
                alert(fileValidation.message);
                return;
            }

            if (!text && !fileValidation.metadata) {
                alert("Пожалуйста, введите сообщение или прикрепите файл.");
                return;
            }
            
            let sender = 'user';
            let nextView = 'user-detail';

            if (isAdmin) {
                 nextView = 'admin-detail';
                 if (document.getElementById('reply-as-staff')?.checked) {
                     sender = 'staff';
                 }
            } else {
                 // If user is accessing the old full detail view, redirect them back to the portal view upon reply
                 nextView = 'user-portal';
            }
            
            addMessageToTicket(ticketId, sender, text, fileValidation.metadata); // Passing metadata
            
            // Logic for status change upon reply
            if (sender === 'staff' && ticket.status !== 'Closed') {
                 // Staff reply moves it to In Progress (or keeps it there)
                 updateTicket(ticketId, { status: 'In Progress' });
            } else if (sender === 'user' && ticket.status !== 'Closed') {
                 // User reply moves it to Open, potentially changing it from 'Awaiting User Response'
                 updateTicket(ticketId, { status: 'Open' }); 
            }

            textInput.value = '';
            attachmentInput.value = ''; // Clear file input
            navigateTo(nextView, ticketId);
        });
    }

    function updateTicket(id, updates) {
        const index = tickets.findIndex(t => t.id === id);
        if (index > -1) {
            
            // Logic to unpin if status changes to 'Closed'
            if (updates.status === 'Closed') {
                updates.isPinned = false;
            }
            
            tickets[index] = { ...tickets[index], ...updates, updatedAt: Date.now() };
            saveTickets(tickets);
        }
    }
    
    function toggleTicketPin(id) {
        const index = tickets.findIndex(t => t.id === id);
        if (index > -1) {
            const currentPinStatus = tickets[index].isPinned || false;
            tickets[index].isPinned = !currentPinStatus;
            saveTickets(tickets);
        }
    }
    
    function addMessageToTicket(id, sender, text, attachmentMetadata = null) {
        const ticket = tickets.find(t => t.id === id);
        if (ticket) {
            ticket.messages.push({
                sender: sender,
                text: text,
                timestamp: Date.now(),
                attachment: attachmentMetadata // Store metadata
            });
            // updateTicket handles saving state and updating the 'updatedAt' field
             updateTicket(id, {});
        }
    }

    function renderPaginationControls(totalPages, totalItems, ticketPoolTitle) {
        if (totalPages <= 1) return '';

        const maxPagesToShow = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2));
        let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);
        
        if (endPage - startPage + 1 < maxPagesToShow) {
            startPage = Math.max(1, endPage - maxPagesToShow + 1);
        }

        let pagesHtml = '';
        for (let i = startPage; i <= endPage; i++) {
            pagesHtml += `<button class="page-btn ${i === currentPage ? 'active-page' : ''}" data-page="${i}">${i}</button>`;
        }
        
        // Ensure page numbers are clamped
        const prevPage = Math.max(1, currentPage - 1);
        const nextPage = Math.min(totalPages, currentPage + 1);


        return `
            <div class="card pagination-controls">
                <h3>Страницы обращений (${ticketPoolTitle}: ${totalItems} найдено, ${ticketsPerPage} на странице)</h3>
                <div class="page-buttons">
                    <button class="page-btn" data-page="1" ${currentPage === 1 ? 'disabled' : ''}&laquo; Первая</button>
                    <button class="page-btn" data-page="${prevPage}" ${currentPage === 1 ? 'disabled' : ''}&lsaquo; Предыдущая</button>
                    ${pagesHtml}
                    <button class="page-btn" data-page="${nextPage}" ${currentPage === totalPages ? 'disabled' : ''}>Следующая &rsaquo;</button>
                    <button class="page-btn" data-page="${totalPages}" ${currentPage === totalPages ? 'disabled' : ''}>Последняя &raquo;</button>
                </div>
            </div>
        `;
    }

    function renderAdminPanel() {
        
        appContainer.innerHTML = `<div class="card"><h2>Панель Администратора</h2></div>`;
        
        // --- 1. Data Preparation and Filtering ---

        // Pinned tickets (Active only) are treated separately and displayed first.
        const pinnedTickets = tickets.filter(t => t.isPinned && t.status !== 'Closed').sort((a, b) => b.updatedAt - a.updatedAt);

        // All non-pinned tickets, sorted globally by latest update
        let nonPinnedTickets = tickets.filter(t => !t.isPinned).sort((a, b) => b.updatedAt - a.updatedAt);
        
        // Apply MAX_TICKETS limit (500 latest non-pinned)
        nonPinnedTickets = nonPinnedTickets.slice(0, MAX_TICKETS);
        
        // Sort nonPinnedTickets for display order: Active by Priority/Update, then Closed by Update
        const sortedNonPinnedTickets = nonPinnedTickets.sort((a, b) => {
            const isAClosed = a.status === 'Closed';
            const isBClosed = b.status === 'Closed';
            
            // Closed tickets go last in the combined pool
            if (isAClosed && !isBClosed) return 1;
            if (!isAClosed && isBClosed) return -1;
            
            // If both are active, sort by Priority then Update
            if (!isAClosed && !isBClosed) {
                const priorityOrder = { 'Urgent': 4, 'High': 3, 'Medium': 2, 'Low': 1 };
                const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
                if (priorityDiff !== 0) return priorityDiff;
            }
            
            // Otherwise, sort by latest update
            return b.updatedAt - a.updatedAt;
        });

        // --- 2. Pagination Logic ---

        const totalItems = sortedNonPinnedTickets.length;
        const totalPages = Math.ceil(totalItems / ticketsPerPage);
        
        // Ensure currentPage is valid
        if (currentPage > totalPages && totalPages > 0) {
            currentPage = totalPages;
        } else if (currentPage < 1) {
            currentPage = 1;
        } else if (totalPages === 0) {
            currentPage = 1;
        }

        const startIndex = (currentPage - 1) * ticketsPerPage;
        const endIndex = startIndex + ticketsPerPage;
        const paginatedTickets = sortedNonPinnedTickets.slice(startIndex, endIndex);

        // Separate paginated results back into Active and Closed for distinct rendering sections
        const paginatedActive = paginatedTickets.filter(t => t.status !== 'Closed');
        const paginatedClosed = paginatedTickets.filter(t => t.status === 'Closed');
        
        // Total counts for titles (based on the 500 max pool)
        const totalActiveCount = sortedNonPinnedTickets.filter(t => t.status !== 'Closed').length;
        const totalClosedCount = sortedNonPinnedTickets.filter(t => t.status === 'Closed').length;

        // --- 3. Rendering Controls ---
        
        const pageSizeControls = `
            <div class="card ticket-config-controls">
                <h3>Настройки отображения</h3>
                <label for="tickets-per-page">Тикетов на странице (Макс ${MAX_TICKETS} последних):</label>
                <select id="tickets-per-page">
                    <option value="25" ${ticketsPerPage === 25 ? 'selected' : ''}>25</option>
                    <option value="50" ${ticketsPerPage === 50 ? 'selected' : ''}>50</option>
                    <option value="100" ${ticketsPerPage === 100 ? 'selected' : ''}>100</option>
                </select>
            </div>
        `;
        appContainer.insertAdjacentHTML('beforeend', pageSizeControls);
        
        document.getElementById('tickets-per-page').addEventListener('change', (e) => {
            const newPerPage = parseInt(e.target.value, 10);
            setPaginationParams(newPerPage, 1); // Reset to page 1 on perPage change
        });


        // --- 4. Rendering Lists ---

        // Render Pinned List first (if any)
        if (pinnedTickets.length > 0) {
            const pinnedList = renderTicketList(pinnedTickets, `Закрепленные обращения (${pinnedTickets.length})`, true);
            appContainer.appendChild(pinnedList);
        }

        // Render Active List (Paginated subset)
        const activeTitle = `Активные обращения (Стр. ${currentPage} | Всего ${totalActiveCount})`;
        const openList = renderTicketList(paginatedActive, activeTitle, true);
        appContainer.appendChild(openList);

        // Render Closed List (Paginated subset)
        const closedTitle = `Закрытые обращения (Стр. ${currentPage} | Всего ${totalClosedCount})`;
        const closedList = renderTicketList(paginatedClosed, closedTitle, true);
        appContainer.appendChild(closedList);

        
        // --- 5. Rendering Pagination ---
        
        if (totalItems > 0) {
            const paginationControlsHtml = renderPaginationControls(totalPages, totalItems, `Не закрепленные тикеты (Active + Closed, до ${MAX_TICKETS} последних)`);
            appContainer.insertAdjacentHTML('beforeend', paginationControlsHtml);

            // Add event listeners for pagination buttons
            document.querySelectorAll('.page-btn').forEach(button => {
                button.addEventListener('click', (e) => {
                    const page = e.target.getAttribute('data-page');
                    const newPage = parseInt(page, 10);
                    
                    if (!isNaN(newPage) && newPage >= 1 && newPage <= totalPages) {
                        setPaginationParams(ticketsPerPage, newPage);
                    }
                });
            });
        }
    }
    
    // --- Public Interface ---
    
    return {
        initialize,
        navigateTo,
    };

})();

// Initialize the application when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    TicketSystem.initialize();
});