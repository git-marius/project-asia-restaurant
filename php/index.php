<?php
$host = getenv('MYSQL_HOST') ?: 'mariadb';
$db   = getenv('MYSQL_DATABASE') ?: 'testdb';
$user = getenv('MYSQL_USER') ?: 'testuser';
$pass = getenv('MYSQL_PASSWORD') ?: 'testpass';

echo "<h1>PHP läuft mit Nginx + FPM 🎉</h1>";

$mysqli = @new mysqli($host, $user, $pass, $db);

if ($mysqli->connect_errno) {
    echo "<p style='color:red'>DB-Verbindungsfehler: {$mysqli->connect_error}</p>";
} else {
    echo "<p style='color:green'>DB-Verbindung zu <b>$db</b> erfolgreich!</p>";
}

echo "<h2>Flask API Test (/api/hello)</h2>";
$response = @file_get_contents("http://flask:5000/hello");
if ($response === FALSE) {
    echo "<p style='color:red'>Fehler beim Aufruf von Flask API.</p>";
} else {
    echo "<pre>" . htmlspecialchars($response) . "</pre>";
}
?>
