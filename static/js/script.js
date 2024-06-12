document.addEventListener('DOMContentLoaded', function() {
    fetchUserData();
});

function navigateTo(path) {
    const accessToken = sessionStorage.getItem('accessToken');
    window.location.href = `http://${window.location.host}${path}`;
}

function fetchUserData() {
    const accessToken = sessionStorage.getItem('accessToken');
    if (!accessToken) {
        window.location.href = '/login'; // Redirect to login if no access token
        return;
    }

    fetch(`http://127.0.0.1:5000/api/userdata?access_token=${accessToken}`)
    .then(response => {
        if (!response.ok) throw new Error('Failed to fetch user data');
        return response.json();
    })
    .then(data => {
        document.getElementById('welcomeMessage').textContent = `Selamat Datang, ${data.name}! ${data.role}`;
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to load user data, please login again.');
        window.location.href = '/login';
    });
}

function saveAccessToken(token) {
    sessionStorage.setItem('accessToken', token);
}

function getAccessToken() {
    return sessionStorage.getItem('accessToken');
}

function clearAccessToken() {
    sessionStorage.removeItem('accessToken');
}



function registerUser() {
    const formData = {
        username: document.getElementById('username').value,
        password: document.getElementById('password').value,
        name: document.getElementById('name').value
    };

    fetch('http://localhost:5000/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        window.location.href = '/login';  // Redirect to login page on success
    })
    .catch(error => console.error('Error registering user:', error));
}

function loginUser(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = {
        username: formData.get('username'),
        password: formData.get('password')
    };

    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.accessToken) {
            sessionStorage.setItem('accessToken', data.accessToken);
            window.location.href = '/index';  // Redirect to the main page
        } else {
            throw new Error('Authentication failed');
        }
    })
    .catch(error => {
        console.error('Login Error:', error);
        alert('Login failed. Please check your credentials.');
    });
}



function logoutUser() {
    sessionStorage.clear();
    fetch('/api/logout', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${getAccessToken()}`
        }
    })
    .then(() => {
        window.location.href = '/login';
    })
    .catch(error => console.error('Logout Error:', error));
}


document.getElementById('logoutButton').addEventListener('click', logoutUser);



function loadMedications() {
    const accessToken = sessionStorage.getItem('accessToken'); // Retrieve the stored token
    fetch(`http://localhost:5001/obat?access_token=${accessToken}`)
    .then(response => response.json())
    .then(data => {
        const medicationTableBody = document.getElementById('medication-table-body');
        medicationTableBody.innerHTML = ''; // Clear existing rows
        data.forEach((med, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <th scope="row">${index + 1}</th>
                <td>${med.nama}</td>
                <td>${med.deskripsi}</td>
                <td>${med.kategori}</td>
                <td>${med.tanggal_kedaluwarsa}</td>
                <td>${med.harga}</td>
                <td>${med.jumlah_stok}</td>
                <td>
                    <button onclick="editMedication(${med.id})" class="btn btn-warning">Edit</button>
                    <button onclick="deleteMedication(${med.id})" class="btn btn-danger">Delete</button>
                </td>
            `;
            medicationTableBody.appendChild(row);
        });
    })
    .catch(error => console.error('Error loading medications:', error));
}

document.addEventListener('DOMContentLoaded', loadMedications);


function addMedication(event) {
    event.preventDefault();
    const formData = new FormData(document.getElementById('addMedicationForm'));
    const jsonData = {};
    formData.forEach((value, key) => { jsonData[key] = value; });

    fetch('http://localhost:5001/addObat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(jsonData)
    })
    .then(response => response.json())
    .then(data => {
        alert('Medication added successfully');
        loadMedications(); // Refresh the list
    })
    .catch(error => console.error('Error adding medication:', error));
}

