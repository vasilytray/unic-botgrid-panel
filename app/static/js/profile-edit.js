// Общие функции для редактирования профиля

/// app/static/js/profile-edit.js

// // // console.log('✅ profile-edit.js загружен!');

// Общие функции для редактирования профиля

// Инициализация базовых обработчиков
function initializeBaseHandlers() {
    // // console.log('🔄 Инициализация базовых обработчиков');
    // Обработчик кнопки "Назад"
    const backButtons = document.querySelectorAll('.btn-back, [data-content="profile"]');
    // // console.log(`Найдено кнопок "Назад": ${backButtons.length}`);
    
    backButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            returnToProfile();
        });
    });

    // Автоматически инициализируем модуль безопасности если он присутствует
    initializeSecurityModule();
}

// Функция для возврата к странице профиля
function returnToProfile() {
    // // console.log('🔄 Возврат к профилю');
    if (window.contentManager) {
        // Очищаем кэш профиля для загрузки обновленных данных
        window.contentManager.moduleCache.delete('profile');
        window.contentManager.showModule('profile');
    } else {
        // Fallback
        window.location.href = '/users/profile';
    }
}

// Функции для проверки валидации
function checkNicknameAvailability(inputElement, statusElement) {
    const nick = inputElement.value;
    
    if (!statusElement) return;
    
    if (nick.length < 3) {
        statusElement.innerHTML = '<span class="text-warning">Минимум 3 символа</span>';
        return;
    }
    
    if (!/^[a-zA-Z0-9_]{3,50}$/.test(nick)) {
        statusElement.innerHTML = '<span class="text-danger">Только латинские буквы, цифры и _</span>';
        return;
    }
    
    // Проверка на сервере
    fetch(`/users/check-nickname?nick=${encodeURIComponent(nick)}`)
        .then(response => response.json())
        .then(data => {
            if (data.available) {
                statusElement.innerHTML = '<span class="text-success">✓ Никнейм доступен</span>';
            } else {
                statusElement.innerHTML = '<span class="text-danger">✗ Никнейм уже занят</span>';
            }
        })
        .catch(error => {
            statusElement.innerHTML = '<span class="text-warning">⚠ Ошибка проверки</span>';
        });
}

function checkPasswordMatch(newPasswordInput, confirmPasswordInput, statusElement) {
    const newPassword = newPasswordInput?.value || '';
    const confirmPassword = confirmPasswordInput.value;
    
    if (!statusElement) return;
    
    if (confirmPassword && newPassword !== confirmPassword) {
        statusElement.innerHTML = '<span class="text-danger">✗ Пароли не совпадают</span>';
    } else if (confirmPassword && newPassword === confirmPassword) {
        statusElement.innerHTML = '<span class="text-success">✓ Пароли совпадают</span>';
    } else {
        statusElement.innerHTML = '';
    }
}

// Функции для работы с IP адресами в профиле
function loadSecurityData() {
    // // console.log('🔄 Загрузка данных безопасности...');
    
    // Загружаем текущий IP
    fetch('/users/ip-restrictions/check', {
        credentials: 'include'
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // console.log('✅ Получены данные IP:', data);
            
            const currentIpElement = document.getElementById('security-current-ip');
            if (currentIpElement) {
                currentIpElement.textContent = data.ip_address;
                // console.log('✅ Текущий IP установлен:', data.ip_address);
            } else {
                console.error('❌ Элемент security-current-ip не найден');
            }
        })
        .catch(error => {
            console.error('❌ Ошибка загрузки текущего IP:', error);
            const currentIpElement = document.getElementById('security-current-ip');
            if (currentIpElement) {
                currentIpElement.textContent = 'Ошибка загрузки';
            }
        });
    
    // Загружаем список разрешенных IP
    loadAllowedIPs();
}

function loadAllowedIPs() {
    const ipList = document.getElementById('allowed-ips-list');
    if (!ipList) {
        console.error('❌ IP list container not found');
        return;
    }
    
    // console.log('🔄 Загрузка списка IP...');
    ipList.innerHTML = '<div class="loading-ips"><i class="fas fa-spinner fa-spin"></i> Загрузка IP адресов...</div>';
    
    fetch('/users/ip-restrictions/ips', {
        credentials: 'include'
    })
        .then(response => {
            // console.log('📥 Ответ сервера на запрос IP:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(ips => {
            // console.log('✅ Получены IP адреса:', ips);
            
            if (ips.length === 0) {
                ipList.innerHTML = '<p class="text-muted">Нет разрешенных IP адресов</p>';
                // console.log('ℹ️ Нет разрешенных IP адресов');
            } else {
                ipList.innerHTML = ips.map(ip => `
                    <div class="ip-item" data-ip="${ip.ip_address}">
                        <span class="ip-address">${ip.ip_address}</span>
                        <span class="ip-description">${ip.description || 'Без описания'}</span>
                        <button class="btn btn-danger btn-sm" data-ip="${ip.ip_address}">
                            <i class="fas fa-trash"></i> Удалить
                        </button>
                    </div>
                `).join('');
                
                // console.log(`✅ Отображено ${ips.length} IP адресов`);
                
                // Переинициализируем обработчики событий для новых кнопок
                setTimeout(() => {
                    const deleteButtons = ipList.querySelectorAll('.btn-danger');
                    // console.log(`🔄 Инициализация ${deleteButtons.length} кнопок удаления`);
                    
                    deleteButtons.forEach(button => {
                        // Удаляем старые обработчики
                        button.replaceWith(button.cloneNode(true));
                    });
                    
                    // Добавляем новые обработчики
                    ipList.querySelectorAll('.btn-danger').forEach(button => {
                        button.addEventListener('click', function(e) {
                            e.preventDefault();
                            const ip = this.dataset.ip;
                            // console.log('🗑️ Удаление IP:', ip);
                            removeIP(ip);
                        });
                    });
                }, 100);
            }
        })
        .catch(error => {
            console.error('❌ Ошибка загрузки IPs:', error);
            ipList.innerHTML = '<p class="text-danger">Ошибка загрузки IP адресов: ' + error.message + '</p>';
        });
}

function addCurrentIP() {
    // console.log('➕ Добавление текущего IP');
    const currentIpElement = document.getElementById('security-current-ip');
    const ipInput = document.getElementById('new-ip-address');
    
    if (currentIpElement && ipInput && currentIpElement.textContent && 
        currentIpElement.textContent !== 'Определяется...' && 
        currentIpElement.textContent !== 'Ошибка загрузки') {
        
        ipInput.value = currentIpElement.textContent;
        openAddIPModal();
        // console.log('✅ Текущий IP установлен в форму:', currentIpElement.textContent);
    } else {
        console.error('❌ Не удалось определить текущий IP');
        showNotification('Не удалось определить текущий IP адрес', 'error');
    }
}

function openAddIPModal() {
    const modal = document.getElementById('addIPModal');
    if (modal) {
        modal.style.display = 'block';
        // console.log('✅ Модальное окно открыто');
    }
}

function closeAddIPModal() {
    const modal = document.getElementById('addIPModal');
    if (modal) {
        modal.style.display = 'none';
    }
    
    const form = document.getElementById('addIPForm');
    if (form) {
        form.reset();
    }
    // console.log('✅ Модальное окно закрыто');
}

async function addNewIP(formElement) {
    // console.log('🔄 Добавление нового IP...');
    const form = formElement.closest('form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // console.log('📤 Данные для отправки:', data);
    
    // Валидация IP адреса
    if (!data.ip_address || !isValidIP(data.ip_address)) {
        showNotification('Неверный формат IP адреса', 'error');
        return;
    }
    
    try {
        const response = await fetch('/users/ip-restrictions/ip', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
            credentials: 'include'
        });
        
        // console.log('📥 Ответ сервера:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Ошибка при добавлении IP адреса');
        }
        
        const result = await response.json();
        // console.log('✅ IP добавлен:', result);
        showNotification(result.message || 'IP адрес успешно добавлен', 'success');
        
        closeAddIPModal();
        loadAllowedIPs(); // Перезагружаем список
        
    } catch (error) {
        console.error('❌ Ошибка добавления IP:', error);
        showNotification(error.message || 'Ошибка при добавлении IP адреса', 'error');
    }
}

async function removeIP(ipAddress) {
    if (!ipAddress) {
        console.error('IP address is required for removal');
        showNotification('Ошибка: IP адрес не указан', 'error');
        return;
    }
    
    // console.log('🔄 Удаление IP:', ipAddress);
    
    if (!confirm(`Вы уверены, что хотите удалить IP адрес ${ipAddress}?`)) {
        return;
    }
    
    try {
        const response = await fetch('/users/ip-restrictions/ip', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ip_address: ipAddress }),
            credentials: 'include'
        });
        
        // console.log('📥 Ответ сервера на удаление:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Ошибка при удалении IP адреса');
        }
        
        const result = await response.json();
        // console.log('✅ IP удален:', result);
        showNotification(result.message || 'IP адрес удален', 'success');
        
        // Перезагружаем список IP
        loadAllowedIPs();
        
    } catch (error) {
        console.error('❌ Ошибка удаления IP:', error);
        showNotification(error.message || 'Ошибка при удалении IP адреса', 'error');
    }
}

// Вспомогательная функция для валидации IP
function isValidIP(ip) {
    if (!ip) return false;
    
    // IPv4 regex
    const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
    // IPv6 regex (упрощенный)
    const ipv6Regex = /^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/;
    
    if (ipv4Regex.test(ip)) {
        // Проверяем, что каждый октет в диапазоне 0-255
        const parts = ip.split('.');
        return parts.every(part => {
            const num = parseInt(part, 10);
            return num >= 0 && num <= 255;
        });
    }
    
    return ipv6Regex.test(ip);
}

// Инициализация IP обработчиков безопасности
function initializeSecurityHandlers() {
    // console.log('🔄 Инициализация обработчиков безопасности...');
    
    // Обработчик модального окна
    const modal = document.getElementById('addIPModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this || e.target.classList.contains('close') || 
                e.target.dataset.action === 'close-add-ip-modal') {
                closeAddIPModal();
            }
        });
        
        // Предотвращаем закрытие при клике на содержимое
        modal.querySelector('.modal-content').addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }
    
    // Обработчик формы добавления IP
    const ipForm = document.getElementById('addIPForm');
    if (ipForm) {
        ipForm.addEventListener('submit', function(e) {
            e.preventDefault();
            addNewIP(this);
        });
    }
    
    // Загружаем данные безопасности при инициализации
    loadSecurityData();
}

// Автоматическая инициализация при загрузке модуля безопасности
function initializeSecurityModule() {
    // console.log('🔄 Инициализация модуля безопасности...');
    
    // Проверяем, находимся ли мы на странице безопасности
    const securitySection = document.querySelector('.security-sections');
    if (securitySection) {
        // console.log('✅ Найдена секция безопасности, инициализируем...');
        initializeSecurityHandlers();
        
        // Принудительно загружаем данные безопасности
        setTimeout(() => {
            loadSecurityData();
        }, 100);
    }
}

// Основные функции для работы с профилем
async function updateBasicProfile(formElement) {
    // console.log('🔄 updateBasicProfile вызвана из profile-edit.js');
    
    const form = formElement.closest('form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // console.log('📤 Отправка данных:', data);
    
    // Клиентская проверка дополнительного email
    const emailStatus = document.getElementById('secondary-email-availability');
    if (data.secondary_email && emailStatus) {
        const statusText = emailStatus.textContent || '';
        if (statusText.includes('✗') || statusText.includes('Неверный формат')) {
            if (typeof window.showNotification === 'function') {
                window.showNotification('Пожалуйста, исправьте ошибки в дополнительном email', 'error');
            }
            return;
        }
        
        if (statusText.includes('⏳') || statusText.includes('Проверка')) {
            if (typeof window.showNotification === 'function') {
                window.showNotification('Пожалуйста, дождитесь завершения проверки email', 'error');
            }
            return;
        }
    }
    
    try {
        const response = await fetch('/users/profile/', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        // console.log('📥 Ответ сервера:', response.status);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Ошибка при обновлении профиля');
        }
        
        const result = await response.json();
        // console.log('✅ Обновление успешно:', result);
        
        if (typeof window.showNotification === 'function') {
            window.showNotification(result.message || 'Профиль успешно обновлен', 'success');
        }
        
        returnToProfile();
        
    } catch (error) {
        console.error('❌ Ошибка обновления профиля:', error);
        if (typeof window.showNotification === 'function') {
            window.showNotification(error.message || 'Ошибка при обновлении профиля', 'error');
        }
    }
}

async function changePassword(formElement) {
    // console.log('changePassword called from profile-edit.js');

    const form = formElement.closest('form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // Клиентская проверка паролей
    if (data.new_password !== data.confirm_password) {
        showNotification('Новый пароль и подтверждение не совпадают', 'error');
        return;
    }
    
    if (data.current_password === data.new_password) {
        showNotification('Новый пароль должен отличаться от текущего', 'error');
        return;
    }
    
    try {
        const response = await fetch('/users/change-password/', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Ошибка при смене пароля');
        }
        
        const result = await response.json();
        showNotification(result.message || 'Пароль успешно изменен', 'success');
        
        // Очищаем форму
        form.reset();
        const matchElement = document.getElementById('password-match');
        if (matchElement) {
            matchElement.innerHTML = '';
        }

        // Возвращаемся к профилю
        // console.log('🔄 Возвращаемся к профилю после смены пароля');
        returnToProfile();
        
    } catch (error) {
        console.error('Error changing password:', error);
        showNotification(error.message || 'Ошибка при смене пароля', 'error');
    }
}

// Проверяем, что функции существуют в глобальной области видимости
if (typeof window.handleAction === 'undefined') {
    window.handleAction = function(action, element, event = null) {
        // console.log('Fallback handleAction called:', action);
        // Базовая реализация для случаев, когда основной handleAction не загружен
        if (event && event.preventDefault) {
            event.preventDefault();
        }
        
        // Обрабатываем действия, специфичные для редактирования профиля
        switch(action) {
            case 'save-basic-profile':
                updateBasicProfile(element);
                break;
            case 'change-password':
                changePassword(element);
                break;
            case 'add-current-ip':
                addCurrentIP();
                break;
            case 'open-add-ip-modal':
                openAddIPModal();
                break;
            case 'close-add-ip-modal':
                closeAddIPModal();
                break;
            case 'add-new-ip':
                addNewIP(element);
                break;
            case 'remove-ip':
                const ipAddress = element.dataset.ip;
                removeIP(ipAddress);
                break;
            default:
                console.warn('Неизвестное действие в profile-edit:', action);
        }
    };
}

// function showNotification(message, type = 'info') {
//     // Используем глобальную функцию showNotification из script.js если доступна
//     if (typeof window.showNotification === 'function' && window.showNotification !== showNotification) {
//         window.showNotification(message, type);
//         return;
//     }
    
//     // Fallback уведомление если глобальная функция недоступна
//     // console.log(`📢 ${type.toUpperCase()}: ${message}`);
    
//     // Создаем простое уведомление
//     const notification = document.createElement('div');
//     notification.style.cssText = `
//         position: fixed;
//         top: 20px;
//         right: 20px;
//         padding: 15px 20px;
//         border-radius: 8px;
//         color: white;
//         z-index: 10000;
//         font-weight: bold;
//         box-shadow: 0 4px 12px rgba(0,0,0,0.15);
//         ${type === 'success' ? 'background: #28a745;' : 
//           type === 'error' ? 'background: #dc3545;' : 
//           'background: #17a2b8;'}
//     `;
//     notification.textContent = message;
    
//     document.body.appendChild(notification);
    
//     // Удаляем уведомление через 4 секунды
//     setTimeout(() => {
//         if (notification.parentNode) {
//             notification.remove();
//         }
//     }, 4000);
// }

// Убедимся, что все функции зарегистрированы глобально
function registerGlobalFunctions() {
    // console.log('🌐 Регистрация глобальных функций...');
    
    // Регистрируем все функции как глобальные
    const functionsToRegister = {
        'updateBasicProfile': updateBasicProfile,
        'changePassword': changePassword,
        'addCurrentIP': addCurrentIP,
        'openAddIPModal': openAddIPModal,
        'closeAddIPModal': closeAddIPModal,
        'addNewIP': addNewIP,
        'removeIP': removeIP,
        'returnToProfile': returnToProfile,
        'loadSecurityData': loadSecurityData,
        'loadAllowedIPs': loadAllowedIPs,
        'initializeSecurityHandlers': initializeSecurityHandlers,
        'initializeBaseHandlers': initializeBaseHandlers
    };
    
    Object.entries(functionsToRegister).forEach(([name, func]) => {
        if (typeof func === 'function') {
            window[name] = func;
            // console.log(`✅ Зарегистрирована функция: ${name}`);
        } else {
            console.error(`❌ Функция ${name} не найдена для регистрации`);
        }
    });
    
    // console.log('✅ Все функции зарегистрированы глобально');
}

// Вызываем регистрацию при загрузке
registerGlobalFunctions();

// Также регистрируем при загрузке DOM на всякий случай
document.addEventListener('DOMContentLoaded', function() {
    // console.log('📄 DOM загружен, проверяем регистрацию функций...');
    registerGlobalFunctions();
    initializeBaseHandlers();
});

// // Обновляем глобальную регистрацию функций
// // console.log('🌐 Регистрируем глобальные функции...');
// window.updateBasicProfile = updateBasicProfile;
// window.changePassword = changePassword;
// window.addCurrentIP = addCurrentIP;
// window.openAddIPModal = openAddIPModal;
// window.closeAddIPModal = closeAddIPModal;
// window.addNewIP = addNewIP;
// window.removeIP = removeIP;
// window.checkCurrentIP = checkCurrentIP;
// window.returnToProfile = returnToProfile;
// window.loadSecurityData = loadSecurityData;
// window.loadAllowedIPs = loadAllowedIPs;
// window.initializeSecurityHandlers = initializeSecurityHandlers;

// // console.log('✅ Все функции зарегистрированы глобально');