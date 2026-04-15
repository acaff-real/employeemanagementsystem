const API_URL = "http://127.0.0.1:8000";
window.onload = checkAuth;
let currentUser = null; 

async function checkAuth() {
    const token = localStorage.getItem("token");
    if (token) {
        const response = await fetch(`${API_URL}/users/me`, { headers: getAuthHeaders() });
        
        if (response.ok) {
            currentUser = await response.json();
            document.getElementById("login-section").classList.add("hidden");
            document.getElementById("app-section").classList.remove("hidden");
            document.getElementById("logout-btn").classList.remove("hidden");
            
            const addEmployeeForm = document.getElementById("add-employee-form");
            if (currentUser.is_admin) {
                addEmployeeForm.classList.remove("hidden");
            } else {
                addEmployeeForm.classList.add("hidden");
            }
            loadDashboard();
        } else {
            logout();
        }
    } else {
        document.getElementById("login-section").classList.remove("hidden");
        document.getElementById("app-section").classList.add("hidden");
        document.getElementById("logout-btn").classList.add("hidden");
    }
}

async function loadDashboard() {
    const response = await fetch(`${API_URL}/employees/`);
    const employees = await response.json();
    
    const dashboard = document.getElementById('dashboard');
    dashboard.innerHTML = ''; 

    employees.forEach(emp => {
        const safeTasks = emp.tasks || [];
        
        let tasksHTML = safeTasks.map(task => {
            const safeComments = task.comments || [];
            
            let commentsHTML = safeComments.map(c => {
                const authorName = c.author ? c.author.username : 'Unknown';
                return `
                    <div class="text-xs text-gray-700 border-l-4 border-gray-300 pl-3 py-1 mt-2">
                        <span class="font-bold text-gray-900">@${authorName}:</span> ${c.text}
                    </div>
                `;
            }).join('');

            return `
                <div class="bg-white p-4 rounded mt-3 border-2 border-gray-200">
                    <div class="flex justify-between items-center mb-2">
                        <span class="${task.status === 'Completed' ? 'line-through text-gray-400' : 'text-gray-900 font-medium'}">${task.description}</span>
                        ${task.status !== 'Completed' 
                            ? `<button onclick="completeTask(${task.id})" class="text-xs border border-green-600 text-green-700 hover:bg-green-50 px-3 py-1 rounded">Finish</button>` 
                            : `<span class="text-xs text-green-600 font-bold">Done ✓</span>`}
                    </div>
                    
                    <div class="mb-3">${commentsHTML}</div>
                    
                    <div class="flex flex-col sm:flex-row gap-2 mt-2">
                        <input type="text" id="comment-desc-${task.id}" placeholder="Type a comment..." class="border-2 border-gray-200 p-2 rounded text-xs flex-1 w-full outline-none focus:border-gray-500">
                        <button onclick="addComment(${task.id})" class="border border-gray-800 text-gray-800 text-xs px-4 py-2 rounded hover:bg-gray-100 w-full sm:w-auto">Reply</button>
                    </div>
                </div>
            `;
        }).join('');

        let promoteBtn = currentUser.is_admin && !emp.is_admin 
            ? `<button onclick="promoteEmployee(${emp.id})" class="text-xs font-semibold text-gray-500 hover:text-gray-900 mr-3">MAKE ADMIN</button>`
            : '';

        let deleteBtn = currentUser.is_admin && currentUser.id !== emp.id 
            ? `<button onclick="deleteEmployee(${emp.id})" class="text-xs font-semibold text-red-500 hover:text-red-700">DELETE</button>`
            : '';

        let canAssignTask = currentUser.is_admin || currentUser.id === emp.id;
        
        let assignTaskHTML = canAssignTask ? `
            <div class="flex flex-col sm:flex-row gap-2 mt-4 pt-4 border-t-2 border-gray-100">
                <input type="text" id="task-desc-${emp.id}" placeholder="New task..." class="border-2 border-gray-200 p-2 rounded text-sm flex-1 w-full outline-none focus:border-gray-800">
                <button onclick="addTask(${emp.id})" class="bg-gray-800 text-white text-sm px-4 py-2 rounded w-full sm:w-auto hover:bg-gray-900">Assign</button>
            </div>
        ` : '';

        
        dashboard.innerHTML += `
            <div class="bg-white p-6 rounded-lg border-2 border-gray-300 relative">
                <div class="absolute top-4 right-4">${promoteBtn} ${deleteBtn}</div>
                <h3 class="text-lg font-bold text-gray-900">${emp.name} 
                    <span class="text-xs font-normal ${emp.is_admin ? 'text-red-600 font-bold' : 'text-gray-500'}">
                        (@${emp.username}) ${emp.is_admin ? '[SUDO]' : ''}
                    </span>
                </h3>
                <p class="text-sm text-gray-600 mb-4">${emp.role}</p>
                <div class="mb-4">
                    <h4 class="font-semibold text-sm text-gray-500 tracking-wider uppercase mb-2">Current Tasks</h4>
                    ${tasksHTML || '<p class="text-sm text-gray-400">No tasks assigned.</p>'}
                </div>
                ${assignTaskHTML}
            </div>
        `;
    });
}



async function login() {
    const usernameInput = document.getElementById("login-username").value;
    const passwordInput = document.getElementById("login-password").value;
    const formData = new URLSearchParams();
    formData.append("username", usernameInput);
    formData.append("password", passwordInput);

    const response = await fetch(`${API_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData
    });

    if (response.ok) {
        const data = await response.json();
        localStorage.setItem("token", data.access_token);
        checkAuth();
    } else {
        alert("Invalid username or password");
    }
}

function logout() {
    localStorage.removeItem("token");
    checkAuth();
}

function getAuthHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${localStorage.getItem("token")}`
    };
}

async function addEmployee() {
    const nameInput = document.getElementById('emp-name');
    const roleInput = document.getElementById('emp-role');
    const usernameInput = document.getElementById('emp-username');
    const passwordInput = document.getElementById('emp-password');
    const isAdminInput = document.getElementById('emp-is-admin'); 
    
    await fetch(`${API_URL}/employees/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ 
            name: nameInput.value, 
            role: roleInput.value,
            username: usernameInput.value,
            password: passwordInput.value,
            is_admin: isAdminInput.checked 
        })
    });

    nameInput.value = ''; roleInput.value = ''; usernameInput.value = ''; passwordInput.value = '';
    isAdminInput.checked = false;
    loadDashboard(); 
}

async function deleteEmployee(employeeId) {
    if(!confirm("Are you sure you want to delete this employee?")) return;
    await fetch(`${API_URL}/employees/${employeeId}`, { method: 'DELETE', headers: getAuthHeaders() });
    loadDashboard();
}

async function promoteEmployee(employeeId) {
    if(!confirm("Are you sure you want to grant this user Sudo privileges?")) return;
    await fetch(`${API_URL}/employees/${employeeId}/promote`, { method: 'PUT', headers: getAuthHeaders() });
    loadDashboard();
}

async function addTask(employeeId) {
    const descInput = document.getElementById(`task-desc-${employeeId}`);
    if (!descInput.value) return;
    await fetch(`${API_URL}/tasks/`, {
        method: 'POST', headers: getAuthHeaders(), body: JSON.stringify({ description: descInput.value, employee_id: employeeId })
    });
    loadDashboard(); 
}

async function completeTask(taskId) {
    await fetch(`${API_URL}/tasks/${taskId}`, {
        method: 'PUT', headers: getAuthHeaders(), body: JSON.stringify({ status: 'Completed' })
    });
    loadDashboard();
}

async function addComment(taskId) {
    const textInput = document.getElementById(`comment-desc-${taskId}`);
    if (!textInput.value) return;
    const response = await fetch(`${API_URL}/tasks/${taskId}/comments`, {
        method: 'POST', headers: getAuthHeaders(), body: JSON.stringify({ text: textInput.value })
    });
    if (response.ok) loadDashboard(); 
    else alert("Something went wrong adding your comment!");
}