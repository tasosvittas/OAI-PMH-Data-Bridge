<?php
/**
 * Simple API endpoint to import records
 * Called by Bridge via HTTP
 */

require_once __DIR__ . '/../vendor/autoload.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    die(json_encode(['error' => 'Method not allowed']));
}

$identifier = $_POST['identifier'] ?? null;
$metadataPrefix = $_POST['metadataPrefix'] ?? 'oai_dc';
$xmlContent = $_POST['content'] ?? null;

if (!$identifier || !$xmlContent) {
    http_response_code(400);
    die(json_encode(['error' => 'Missing required parameters']));
}

try {
    // Save XML to temp file
    $tempFile = sys_get_temp_dir() . '/oai_' . uniqid() . '.xml';
    file_put_contents($tempFile, $xmlContent);
    
    // Execute CLI command
    $cliPath = __DIR__ . '/../bin/cli';
    $cmd = sprintf(
        'php %s oai:add:record %s %s %s --no-interaction 2>&1',
        escapeshellarg($cliPath),
        escapeshellarg($identifier),
        escapeshellarg($metadataPrefix),
        escapeshellarg($tempFile)
    );
    
    $output = [];
    $returnCode = 0;
    exec($cmd, $output, $returnCode);
    
    // Clean up
    @unlink($tempFile);
    
    if ($returnCode === 0) {
        echo json_encode([
            'status' => 'success',
            'identifier' => $identifier,
            'output' => implode("\n", $output)
        ]);
    } else {
        http_response_code(500);
        echo json_encode([
            'status' => 'error',
            'identifier' => $identifier,
            'output' => implode("\n", $output)
        ]);
    }
    
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'status' => 'error',
        'message' => $e->getMessage()
    ]);
}
