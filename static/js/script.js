/*!
* Start Bootstrap - Agency v7.0.12 (https://startbootstrap.com/theme/agency)
* Copyright 2013-2023 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-agency/blob/master/LICENSE)
*/
//
// Scripts
// 



window.addEventListener('DOMContentLoaded', event => {

    // Navbar shrink function
    var navbarShrink = function () {
        const navbarCollapsible = document.body.querySelector('#mainNav');
        if (!navbarCollapsible) {
            return;
        }
        if (window.scrollY === 0) {
            navbarCollapsible.classList.remove('navbar-shrink')
        } else {
            navbarCollapsible.classList.add('navbar-shrink')
        }

    };

    // Shrink the navbar 
    navbarShrink();

    // Shrink the navbar when page is scrolled
    document.addEventListener('scroll', navbarShrink);

    //  Activate Bootstrap scrollspy on the main nav element
    const mainNav = document.body.querySelector('#mainNav');
    if (mainNav) {
        new bootstrap.ScrollSpy(document.body, {
            target: '#mainNav',
            rootMargin: '0px 0px -40%',
        });
    };

    // Collapse responsive navbar when toggler is visible
    const navbarToggler = document.body.querySelector('.navbar-toggler');
    const responsiveNavItems = [].slice.call(
        document.querySelectorAll('#navbarResponsive .nav-link')
    );
    responsiveNavItems.map(function (responsiveNavItem) {
        responsiveNavItem.addEventListener('click', () => {
            if (window.getComputedStyle(navbarToggler).display !== 'none') {
                navbarToggler.click();
            }
        });
    });

});

document.addEventListener('DOMContentLoaded', function() {
    loadDiseases();

    // document.getElementById('add-disease-form').addEventListener('submit', function(event) {
    //     event.preventDefault();
    //     addDisease();
    // });
});

function loadDiseases() {
    fetch('http://localhost:58/diseases')
        .then(response => response.json())
        .then(data => {
            const diseaseTableBody = document.getElementById('disease-table-body');
            diseaseTableBody.innerHTML = '';
            data.forEach((disease, index) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <th scope="row">${index + 1}</th>
                    <td>${disease.name}</td>
                    <td>${disease.description}</td>
                    <td>
                        <button onclick="deleteDisease(${disease.id})" class="btn btn-danger">Delete</button>
                        <button onclick="editDisease(${disease.id})" class="btn btn-warning">Edit</button>
                    </td>
                `;
                diseaseTableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error loading diseases:', error));
}


function addDisease(event) {
    event.preventDefault(); // Prevent default form submission

    const name = document.getElementById('diseaseName').value;
    const description = document.getElementById('diseaseDescription').value;

    fetch('http://localhost:58/diseases', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, description })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        loadDiseases(); // Ensure this function is defined elsewhere to refresh the table
        document.getElementById('add-disease-form').reset();
    })
    .catch(error => console.error('Error adding disease:', error));
}

function deleteDisease(id) {
    fetch(`http://localhost:58/delete_disease?id=${id}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        loadDiseases();
    })
    .catch(error => console.error('Error deleting disease:', error));
}

function editDisease(id) {
    fetch(`http://localhost:58/detail_disease/${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.length > 0) {
                console.log('Data:', data);
                console.log('Data length:', data.length);
                const disease = data[0];
                document.getElementById('editDiseaseName').value = disease.name;
                document.getElementById('editDiseaseDescription').value = disease.description;
                document.getElementById('editDiseaseId').value = disease.id; // Hidden field to store ID
                new bootstrap.Modal(document.getElementById('editDiseaseModal')).show();
            }
        })
        .catch(error => console.error('Error fetching disease details:', error));
}

function submitEditDisease(event) {
    event.preventDefault(); // Prevent default form submission

    const id = document.getElementById('editDiseaseId').value; // Get the disease ID
    const name = document.getElementById('editDiseaseName').value; // Get the updated name
    const description = document.getElementById('editDiseaseDescription').value; // Get the updated description

    fetch(`http://localhost:58/update_disease/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, description })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to update disease');
        }
        return response.json();
    })
    .then(data => {
        alert(data.message);
        new bootstrap.Modal(document.getElementById('editDiseaseModal')).hide(); // Hide the modal after successful update
        loadDiseases(); // Reload the diseases table
    })
    .catch(error => console.error('Error updating disease:', error));
}

document.addEventListener('DOMContentLoaded', function() {
    loadConsultations(); // Load consultations when the page is loaded
});

document.addEventListener('DOMContentLoaded', function() {
    loadConsultations(); // Load consultations when the page is loaded
});

function loadConsultations() {
    fetch('http://localhost:55/konsultasi')
        .then(response => response.json())
        .then(data => {
            const konsultasiTableBody = document.getElementById('konsultasi-table-body');
            konsultasiTableBody.innerHTML = '';
            data.forEach((konsultasi, index) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <th scope="row">${index + 1}</th>
                    <td>${konsultasi.patient_name}</td>
                    <td>${konsultasi.patient_age}</td>
                    <td>${konsultasi.resep_hasil_konsultasi}</td>
                    <td>
                        <button onclick="editConsultation(${konsultasi.id})" class="btn btn-primary">Tambah</button>
                    </td>
                `;
                konsultasiTableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error loading consultations:', error));
}

// Function to add a new consultation
function addConsultation(event) {
    event.preventDefault();

    const nurseId = document.getElementById('nurseId').value;
    const patientId = document.getElementById('patientId').value;
    const patientAge = document.getElementById('patientAge').value;
    const diseaseId = document.getElementById('diseaseId').value;
    const resepKonsultasi = document.getElementById('resepKonsultasi').value;

    // Fetch patient details using patientId
    fetchPatientDetails(patientId)
        .then(data => {
            if (data && data.name) { // Check if data exists and has name property
                const patientName = data.name; // Get the patient name
                const consultationData = {
                    patient_name: patientName, // Include patient name in consultation data
                    patient_age: patientAge,
                    disease_id: diseaseId,
                    nurse_id: nurseId,
                    patient_id: patientId,
                    resep_hasil_konsultasi: resepKonsultasi // Include resep_konsultasi in consultation data
                };
                console.log('Consultation Data:', consultationData)
                // Call the function to submit the consultation data
                submitConsultationAdd(consultationData);
            } else {
                console.error('Patient details not found');
                alert('Patient details not found');
            }
        })
        .catch(error => console.error('Error fetching patient details:', error));
}

function editConsultation(id) {
    fetch(`http://localhost:55/detail_konsultasi/${id}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Check if data is an array or a single object
            if (Array.isArray(data) && data.length > 0) {
                const consultation = data[0];
                document.getElementById('editConsultationPatientName').value = consultation.patient_name;
                document.getElementById('editConsultationResep').value = consultation.resep_hasil_konsultasi;
                document.getElementById('editConsultationPatientAge').value = consultation.patient_age;
                document.getElementById('editConsultationDiseaseId').value = consultation.disease_id;
                document.getElementById('editConsultationNurseId').value = consultation.nurse_id;
                document.getElementById('editConsultationPatientId').value = consultation.patient_id;
                document.getElementById('editConsultationId').value = consultation.id; // Hidden field to store ID

                // Trigger Bootstrap modal manually
                const modal = new bootstrap.Modal(document.getElementById('editConsultationModal'));
                modal.show();
            } else if (!Array.isArray(data) && data !== null) {
                // Handle single object response
                const consultation = data;
                document.getElementById('editConsultationPatientName').value = consultation.patient_name;
                document.getElementById('editConsultationResep').value = consultation.resep_hasil_konsultasi;
                document.getElementById('editConsultationPatientAge').value = consultation.patient_age;
                document.getElementById('editConsultationDiseaseId').value = consultation.disease_id;
                document.getElementById('editConsultationNurseId').value = consultation.nurse_id;
                document.getElementById('editConsultationPatientId').value = consultation.patient_id;
                document.getElementById('editConsultationId').value = consultation.id; // Hidden field to store ID

                // Trigger Bootstrap modal manually
                const modal = new bootstrap.Modal(document.getElementById('editConsultationModal'));
                modal.show();
            } else {
                console.error('No consultation data found');
            }
        })
        .catch(error => console.error('Error fetching consultation details:', error));
}


document.getElementById('editConsultationPatientId').addEventListener('change', function() {
    const patientId = this.value;
    if (patientId) {
        fetch(`http://localhost:50/detail_user/${patientId}`)
            .then(response => response.json())
            .then(data => {
                if (data && data.name) {
                    document.getElementById('editConsultationPatientName').value = data.name;
                } else {
                    document.getElementById('editConsultationPatientName').value = '';
                    alert('Patient details not found');
                }
            })
            .catch(error => console.error('Error fetching patient details:', error));
    } else {
        document.getElementById('editConsultationPatientName').value = '';
    }
});

document.getElementById('editConsultationPatientId').addEventListener('change', function() {
    const patientId = this.value;
    if (patientId) {
        fetch(`http://localhost:50/detail_user/${patientId}`)
            .then(response => response.json())
            .then(data => {
                if (data && data.name) {
                    document.getElementById('editConsultationPatientName').value = data.name;
                } else {
                    document.getElementById('editConsultationPatientName').value = '';
                    alert('Patient details not found');
                }
            })
            .catch(error => console.error('Error fetching patient details:', error));
    } else {
        document.getElementById('editConsultationPatientName').value = '';
    }
});

// document.getElementById('editConsultationNurseId').addEventListener('change', function() {
//     const nurseId = this.value;
//     if (nurseId) {
//         fetch(`http://localhost:50/detail_user/${nurseId}`)
//             .then(response => response.json())
//             .then(data => {
//                 if (data && data.name) {
//                     document.getElementById('editConsultationNursetName').value = data.name;
//                 } else {
//                     document.getElementById('editConsultationNurseName').value = '';
//                     alert('Nurse details not found');
//                 }
//             })
//             .catch(error => console.error('Error fetching nurse details:', error));
//     } else {
//         document.getElementById('editConsultationPatientName').value = '';
//     }
// });

// Function to fetch patient details based on patient ID
function fetchPatientDetails(patientId) {
    return fetch(`http://localhost:50/detail_user/${patientId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        });
}

// Function to submit consultation data to the server
function submitConsultationAdd(consultationData) {
    fetch('http://localhost:55/konsultasi', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(consultationData)
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        loadConsultations();
        document.getElementById('add-consultation-form').reset();
    })
    .catch(error => console.error('Error adding consultation:', error));
}

// Rest of your script remains the same...



// Function to submit consultation data to the server
function submitConsultationAdd(consultationData) {
    fetch('http://localhost:50/getConsultationsPatientName', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(consultationData)
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        loadConsultations();
        document.getElementById('add-consultation-form').reset();
    })
    .catch(error => console.error('Error adding consultation:', error));
}


function deleteConsultation(id) {
    fetch(`http://localhost:55/delete_konsultasi?id=${id}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        loadConsultations();
    })
    .catch(error => console.error('Error deleting consultation:', error));
}


document.addEventListener('DOMContentLoaded', function() {
    loadJanji(); // Load janji data when the page is loaded
});

function loadJanji() {
    fetch('http://localhost:59/janji')
        .then(response => response.json())
        .then(data => {
            const janjiTableBody = document.getElementById('janji-table-body');
            janjiTableBody.innerHTML = '';
            data.forEach((janji, index) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <th scope="row">${index + 1}</th>
                    <td>${janji.patient_name}</td>
                    <td>${janji.nurse_name}</td>
                    <td>${janji.appointment_date}</td>
                    <td>
                        <button onclick="deleteJanji(${janji.id})" class="btn btn-danger">Delete</button>
                        <button onclick="editJanji(${janji.id})" class="btn btn-warning">Edit</button>
                    </td>
                `;
                janjiTableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error loading janji:', error));
}

function createJanji(event) {
    event.preventDefault();

    const patientName = document.getElementById('patientName').value;
    const nurseName = document.getElementById('nurseName').value;
    const appointmentDate = document.getElementById('appointmentDate').value;
    const nurseId = document.getElementById('idNurse').value;

    fetchPatientId(patientName)
        .then(patientId => {
            // Proceed with creating the janji entry
            return fetch('http://localhost:59/janji', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    patient_name: patientName,
                    nurse_name: nurseName,
                    appointment_date: appointmentDate,
                    nurse_id: nurseId,
                    patient_id: patientId
                })
            });
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.message);
            }
            alert(data.message);
            loadJanji(); // Reload the janji table after successful addition
            document.getElementById('janji-form').reset(); // Reset the form
            // Automatically create a consultation when management_janji is added
            const managementJanjiId = data.management_janji_id;
            fetchPatientId(patientName).then(patientId => createConsultation(patientId, nurseId, managementJanjiId));
        })
        .catch(error => console.error('Error adding management_janji:', error));
}

function fetchPatientId(patientName) {
    return fetch(`http://localhost:59/get_patient_id?name=${encodeURIComponent(patientName)}`)
        .then(response => response.json())
        .then(data => {
            if (data && data.patient_id) {
                return data.patient_id;
            } else {
                throw new Error('Patient ID not found');
            }
        });
}

// Function to create a consultation automatically when a management_janji entry is added
function createConsultation(patientId, nurseId, managementJanjiId) {
    // Fetch patient name based on patientId
    fetch(`http://localhost:50/detail_user/${patientId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data && data.name) { // Check if data exists and has name property
                const patientName = data.name; // Get the patient name
                
                // Include patient name, nurse ID, and management_janji_id in the consultation data
                const consultationData = {
                    patient_id: patientId,
                    patient_name: patientName,
                    nurse_id: nurseId,
                    management_janji_id: managementJanjiId
                    // Include other consultation details here if needed
                };
                
                // Make POST request to create the consultation
                return fetch('http://localhost:55/konsultasi', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(consultationData)
                });
            } else {
                throw new Error('Patient details not found');
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.message);
            }
            console.log(data.message); // Log the message
            // You can perform additional actions after creating the consultation if needed
        })
        .catch(error => console.error('Error creating consultation:', error));
}


function deleteJanji(id) {
    fetch(`http://localhost:59/delete_janji?id=${id}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        loadJanji();
    })
    .catch(error => console.error('Error deleting janji:', error));
}

function editJanji(id) {
    fetch(`http://localhost:59/detail_janji?id=${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.length > 0) {
                const janji = data[0];
                document.getElementById('editJanjiPatientName').value = janji.patient_name;
                document.getElementById('editJanjiNurseName').value = janji.nurse_name;
                document.getElementById('editJanjiAppointmentDate').value = janji.appointment_date;
                // Set the ID for editing
                document.getElementById('editJanjiId').value = janji.id;
                new bootstrap.Modal(document.getElementById('editJanjiModal')).show();
            }
        })
        .catch(error => console.error('Error fetching janji details:', error));
}

function submitEditConsultation(event) {
    event.preventDefault(); // Prevent default form submission

    const id = document.getElementById('editConsultationId').value; // Get the consultation ID
    const patientAge = document.getElementById('editConsultationPatientAge').value;
    const resep = document.getElementById('editConsultationResep').value;
    const diseaseId = document.getElementById('editConsultationDiseaseId').value;
    const nurseId = document.getElementById('editConsultationNurseId').value;
    const patientId = document.getElementById('editConsultationPatientId').value;
    const patientName = document.getElementById('editConsultationPatientName').value; // Get the patient name

    fetch(`http://localhost:55/update_konsultasi/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            patient_age: patientAge,
            disease_id: diseaseId,
            nurse_id: nurseId,
            patient_id: patientId,
            resep_hasil_konsultasi: resep, 
            patient_name: patientName // Include patient name in the update
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to update consultation');
        }
        return response.json();
    })
    .then(data => {
        alert(data.message);
        new bootstrap.Modal(document.getElementById('editConsultationModal')).hide(); // Hide the modal after successful update
        loadConsultations(); // Reload the consultations table
    })
    .catch(error => console.error('Error updating consultation:', error));
}

function submitEditJanji(event) {
    event.preventDefault(); // Prevent default form submission

    const id = document.getElementById('editJanjiId').value; // Get the janji ID
    const patientName = document.getElementById('editJanjiPatientName').value;
    const nurseName = document.getElementById('editJanjiNurseName').value;
    const appointmentDate = document.getElementById('editJanjiAppointmentDate').value;

    fetch(`http://localhost:59/update_janji?id=${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            patient_name: patientName,
            nurse_name: nurseName,
            appointment_date: appointmentDate
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to update janji');
        }
        return response.json();
    })
    .then(data => {
        alert(data.message);
        new bootstrap.Modal(document.getElementById('editJanjiModal')).hide(); // Hide the modal after successful update
        loadJanji(); // Reload the janji table
    })
    .catch(error => console.error('Error updating janji:', error));
}

// Function to fetch nurse name based on nurse ID
function fetchNurseName() {
    const nurseId = document.getElementById('idNurse').value;
    fetch(`http://localhost:59/get_nurse_name?id=${nurseId}`)
        .then(response => response.json())
        .then(data => {
            if (data && data.nurse_name) {
                document.getElementById('nurseName').value = data.nurse_name;
            } else {
                document.getElementById('nurseName').value = '';
                alert('Nurse details not found');
            }
        })
        .catch(error => console.error('Error fetching nurse details:', error));
}

// Call the fetchNurseName function when nurse ID input changes
document.getElementById('idNurse').addEventListener('change', fetchNurseName);