<?php
header('Content-Type: application/json');

// Replace with your actual database credentials
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "your_database_name";

$conn = new mysqli($servername, $username, $password, $dbname);

if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

$sql = "SELECT owner_id, owner_name FROM owners WHERE status = 'attentionneeded'";
$result = $conn->query($sql);

$owners = array();
if ($result->num_rows > 0) {
    while ($row = $result->fetch_assoc()) {
        $owners[] = $row;
    }
}

$conn->close();

echo json_encode($owners);
