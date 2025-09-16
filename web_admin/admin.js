// Admin Panel JavaScript
const API_BASE = 'http://localhost:8001/api';
let selectedFile = null;

// Initialize the admin panel
document.addEventListener('DOMContentLoaded', function() {
    initializeSidebar();
    loadDashboard();
    loadCategories();
});

// Sidebar navigation
function initializeSidebar() {
    const sidebarLinks = document.querySelectorAll('.sidebar .nav-link');
    
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links
            sidebarLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Hide all sections
            document.querySelectorAll('.content-section').forEach(section => {
                section.style.display = 'none';
            });
            
            // Show selected section
            const sectionId = this.getAttribute('data-section');
            const section = document.getElementById(sectionId);
            if (section) {
                section.style.display = 'block';
                
                // Load section specific data
                switch(sectionId) {
                    case 'dashboard':
                        loadDashboard();
                        break;
                    case 'files':
                        loadFiles();
                        break;
                    case 'categories':
                        loadCategories();
                        break;
                    case 'users':
                        loadUsers();
                        break;
                    case 'logs':
                        loadLogs();
                        break;
                }
            }
        });
    });
}

// Dashboard functions
async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE}/admin/stats`);
        const stats = await response.json();
        
        document.getElementById('total-files').textContent = stats.total_files || 0;
        document.getElementById('total-users').textContent = stats.total_users || 0;
        document.getElementById('total-downloads').textContent = stats.total_downloads || 0;
        document.getElementById('total-size').textContent = formatFileSize(stats.total_size || 0);
        
        loadRecentActivities();
        loadDailyChart();
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showNotification('خطا در بارگذاری داشبورد', 'error');
    }
}

async function loadRecentActivities() {
    try {
        const response = await fetch(`${API_BASE}/admin/recent-activities`);
        const activities = await response.json();
        
        const container = document.getElementById('recent-activities');
        container.innerHTML = '';
        
        if (activities.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">فعالیت اخیری یافت نشد</p>';
            return;
        }
        
        activities.slice(0, 10).forEach(activity => {
            const item = document.createElement('div');
            item.className = 'border-bottom pb-2 mb-2';
            item.innerHTML = `
                <div class="d-flex justify-content-between">
                    <small class="text-muted">${activity.type}</small>
                    <small class="text-muted">${formatDate(activity.timestamp)}</small>
                </div>
                <div>${activity.description}</div>
            `;
            container.appendChild(item);
        });
    } catch (error) {
        console.error('Error loading recent activities:', error);
        document.getElementById('recent-activities').innerHTML = '<p class="text-danger">خطا در بارگذاری فعالیت‌ها</p>';
    }
}

function loadDailyChart() {
    const ctx = document.getElementById('dailyChart').getContext('2d');
    
    // Sample data - replace with real data from API
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه'],
            datasets: [{
                label: 'دانلودها',
                data: [12, 19, 3, 5, 2, 3, 10],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Files management
async function loadFiles() {
    try {
        const response = await fetch(`${API_BASE}/admin/files`);
        const files = await response.json();
        
        const tbody = document.getElementById('files-table');
        tbody.innerHTML = '';
        
        if (files.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">فایلی یافت نشد</td></tr>';
            return;
        }
        
        files.forEach(file => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <i class="${getFileIcon(file.mime_type)} me-2"></i>
                    ${file.original_name}
                </td>
                <td>${formatFileSize(file.file_size)}</td>
                <td>${file.category_name || 'بدون دسته'}</td>
                <td>${formatDate(file.created_at)}</td>
                <td>${file.download_count || 0}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="generateLinks('${file.id}')">
                        <i class="fas fa-link"></i>
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteFile('${file.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading files:', error);
        showNotification('خطا در بارگذاری فایل‌ها', 'error');
    }
}

function refreshFiles() {
    loadFiles();
    showNotification('فایل‌ها بروزرسانی شدند', 'success');
}

async function deleteFile(fileId) {
    if (!confirm('آیا از حذف این فایل مطمئن هستید؟')) return;
    
    try {
        const response = await fetch(`${API_BASE}/admin/files/${fileId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('فایل با موفقیت حذف شد', 'success');
            loadFiles();
        } else {
            throw new Error('Failed to delete file');
        }
    } catch (error) {
        console.error('Error deleting file:', error);
        showNotification('خطا در حذف فایل', 'error');
    }
}

async function generateLinks(fileId) {
    try {
        const response = await fetch(`${API_BASE}/admin/files/${fileId}/links`, {
            method: 'POST'
        });
        const links = await response.json();
        
        const modal = new bootstrap.Modal(document.createElement('div'));
        // Show links in modal
        showNotification('لینک‌های دانلود تولید شدند', 'success');
    } catch (error) {
        console.error('Error generating links:', error);
        showNotification('خطا در تولید لینک‌ها', 'error');
    }
}

// Categories management
async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE}/admin/categories`);
        const categories = await response.json();
        
        const grid = document.getElementById('categories-grid');
        grid.innerHTML = '';
        
        if (categories.length === 0) {
            grid.innerHTML = '<div class="col-12 text-center text-muted">دسته‌بندی یافت نشد</div>';
            return;
        }
        
        categories.forEach(category => {
            const col = document.createElement('div');
            col.className = 'col-md-4 mb-3';
            col.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">
                            <i class="fas fa-folder me-2"></i>
                            ${category.name}
                        </h5>
                        <p class="card-text">${category.description || 'بدون توضیحات'}</p>
                        <small class="text-muted">تاریخ ایجاد: ${formatDate(category.created_at)}</small>
                        <div class="mt-2">
                            <button class="btn btn-sm btn-primary" onclick="editCategory('${category.id}')">
                                <i class="fas fa-edit"></i> ویرایش
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="deleteCategory('${category.id}')">
                                <i class="fas fa-trash"></i> حذف
                            </button>
                        </div>
                    </div>
                </div>
            `;
            grid.appendChild(col);
        });
        
        // Update category selects
        updateCategorySelects(categories);
    } catch (error) {
        console.error('Error loading categories:', error);
        showNotification('خطا در بارگذاری دسته‌بندی‌ها', 'error');
    }
}

function updateCategorySelects(categories) {
    const selects = ['file-category', 'url-category', 'parent-category'];
    
    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            // Keep first option, remove others
            const options = select.querySelectorAll('option:not(:first-child)');
            options.forEach(option => option.remove());
            
            // Add categories
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.id;
                option.textContent = category.name;
                select.appendChild(option);
            });
        }
    });
}

function showAddCategoryModal() {
    const modal = new bootstrap.Modal(document.getElementById('addCategoryModal'));
    modal.show();
}

async function addCategory() {
    const name = document.getElementById('category-name').value.trim();
    const description = document.getElementById('category-description').value.trim();
    const parentId = document.getElementById('parent-category').value || null;
    
    if (!name) {
        showNotification('نام دسته‌بندی الزامی است', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/admin/categories`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name,
                description,
                parent_id: parentId
            })
        });
        
        if (response.ok) {
            showNotification('دسته‌بندی با موفقیت اضافه شد', 'success');
            document.getElementById('add-category-form').reset();
            bootstrap.Modal.getInstance(document.getElementById('addCategoryModal')).hide();
            loadCategories();
        } else {
            throw new Error('Failed to add category');
        }
    } catch (error) {
        console.error('Error adding category:', error);
        showNotification('خطا در افزودن دسته‌بندی', 'error');
    }
}

async function deleteCategory(categoryId) {
    if (!confirm('آیا از حذف این دسته‌بندی مطمئن هستید؟')) return;
    
    try {
        const response = await fetch(`${API_BASE}/admin/categories/${categoryId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('دسته‌بندی با موفقیت حذف شد', 'success');
            loadCategories();
        } else {
            throw new Error('Failed to delete category');
        }
    } catch (error) {
        console.error('Error deleting category:', error);
        showNotification('خطا در حذف دسته‌بندی', 'error');
    }
}

// File upload functions
function handleFileSelect(input) {
    if (input.files && input.files[0]) {
        selectedFile = input.files[0];
        document.getElementById('file-upload-form').style.display = 'block';
        showNotification(`فایل ${selectedFile.name} انتخاب شد`, 'info');
    }
}

function cancelUpload() {
    selectedFile = null;
    document.getElementById('file-upload-form').style.display = 'none';
    document.getElementById('fileInput').value = '';
}

async function uploadFile() {
    if (!selectedFile) {
        showNotification('لطفاً ابتدا فایل را انتخاب کنید', 'error');
        return;
    }
    
    const categoryId = document.getElementById('file-category').value || null;
    const description = document.getElementById('file-description').value.trim();
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('category_id', categoryId);
    formData.append('description', description);
    
    const progressBar = document.getElementById('upload-progress');
    const progressBarInner = progressBar.querySelector('.progress-bar');
    
    progressBar.style.display = 'block';
    progressBarInner.style.width = '0%';
    
    try {
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                progressBarInner.style.width = percentComplete + '%';
                progressBarInner.textContent = Math.round(percentComplete) + '%';
            }
        });
        
        xhr.addEventListener('load', function() {
            if (xhr.status === 200) {
                showNotification('فایل با موفقیت آپلود شد', 'success');
                cancelUpload();
                progressBar.style.display = 'none';
                loadFiles();
            } else {
                throw new Error('Upload failed');
            }
        });
        
        xhr.addEventListener('error', function() {
            throw new Error('Upload failed');
        });
        
        xhr.open('POST', `${API_BASE}/admin/upload-file`);
        xhr.send(formData);
        
    } catch (error) {
        console.error('Error uploading file:', error);
        showNotification('خطا در آپلود فایل', 'error');
        progressBar.style.display = 'none';
    }
}

async function uploadFromUrl(event) {
    event.preventDefault();
    
    const url = document.getElementById('url-input').value.trim();
    const categoryId = document.getElementById('url-category').value || null;
    const description = document.getElementById('url-description').value.trim();
    
    if (!url) {
        showNotification('لطفاً URL فایل را وارد کنید', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/admin/upload-url`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url,
                category_id: categoryId,
                description
            })
        });
        
        if (response.ok) {
            showNotification('فایل از URL با موفقیت آپلود شد', 'success');
            document.getElementById('url-input').value = '';
            document.getElementById('url-description').value = '';
            loadFiles();
        } else {
            throw new Error('URL upload failed');
        }
    } catch (error) {
        console.error('Error uploading from URL:', error);
        showNotification('خطا در آپلود از URL', 'error');
    }
}

// Users management
async function loadUsers() {
    try {
        const response = await fetch(`${API_BASE}/admin/users`);
        const users = await response.json();
        
        const tbody = document.getElementById('users-table');
        tbody.innerHTML = '';
        
        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">کاربری یافت نشد</td></tr>';
            return;
        }
        
        users.forEach(user => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${user.id}</td>
                <td>
                    <span class="badge ${user.is_verified ? 'bg-success' : 'bg-warning'}">
                        ${user.is_verified ? 'تأیید شده' : 'تأیید نشده'}
                    </span>
                </td>
                <td>${formatDate(user.created_at)}</td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.id})">
                        <i class="fas fa-trash"></i> حذف
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading users:', error);
        showNotification('خطا در بارگذاری کاربران', 'error');
    }
}

async function deleteUser(userId) {
    if (!confirm('آیا از حذف این کاربر مطمئن هستید؟')) return;
    
    try {
        const response = await fetch(`${API_BASE}/admin/users/${userId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('کاربر با موفقیت حذف شد', 'success');
            loadUsers();
        } else {
            throw new Error('Failed to delete user');
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        showNotification('خطا در حذف کاربر', 'error');
    }
}

// Logs
async function loadLogs() {
    try {
        const response = await fetch(`${API_BASE}/admin/logs`);
        const logs = await response.text();
        
        document.getElementById('logs-content').textContent = logs;
    } catch (error) {
        console.error('Error loading logs:', error);
        document.getElementById('logs-content').textContent = 'خطا در بارگذاری لاگ‌ها';
    }
}

function refreshLogs() {
    loadLogs();
    showNotification('لاگ‌ها بروزرسانی شدند', 'success');
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('fa-IR');
}

function getFileIcon(mimeType) {
    if (!mimeType) return 'fas fa-file';
    
    if (mimeType.startsWith('image/')) return 'fas fa-image text-primary';
    if (mimeType.startsWith('video/')) return 'fas fa-video text-danger';
    if (mimeType.startsWith('audio/')) return 'fas fa-music text-success';
    if (mimeType === 'application/pdf') return 'fas fa-file-pdf text-danger';
    if (mimeType.includes('zip') || mimeType.includes('rar')) return 'fas fa-file-archive text-warning';
    if (mimeType.startsWith('text/')) return 'fas fa-file-alt text-info';
    
    return 'fas fa-file text-secondary';
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}