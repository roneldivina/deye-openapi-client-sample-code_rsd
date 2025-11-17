<?php

class DeyeInverterClient
{
    private $apiUrl;
    private $apiKey;
    private $deviceSn;

    public function __construct($apiUrl, $apiKey, $deviceSn)
    {
        $this->apiUrl = $apiUrl;
        $this->apiKey = $apiKey;
        $this->deviceSn = $deviceSn;
    }

    public function getDeviceData()
    {
        $endpoint = $this->apiUrl . '/device/query';

        $payload = [
            'device_sn' => $this->deviceSn,
        ];

        return $this->makeRequest($endpoint, $payload);
    }

    public function getEnergyData($dateFrom = null, $dateTo = null)
    {
        $endpoint = $this->apiUrl . '/energy/query';

        $payload = [
            'device_sn' => $this->deviceSn,
            'begin_date' => $dateFrom ?? date('Y-m-d', strtotime('-1 day')),
            'end_date' => $dateTo ?? date('Y-m-d'),
        ];

        return $this->makeRequest($endpoint, $payload);
    }

    public function getRealTimeData()
    {
        $endpoint = $this->apiUrl . '/device/realtime';

        $payload = [
            'device_sn' => $this->deviceSn,
        ];

        return $this->makeRequest($endpoint, $payload);
    }

    private function makeRequest($endpoint, $payload)
    {
        $ch = curl_init($endpoint);

        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payload));
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: application/json',
            'Authorization: Bearer ' . $this->apiKey,
        ]);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode === 200) {
            return json_decode($response, true);
        }

        return ['error' => 'Request failed', 'code' => $httpCode];
    }
}

// Usage example
$client = new DeyeInverterClient(
    'https://api.example.com',
    'your_api_key_here',
    'device_serial_number'
);

$realtimeData = $client->getRealTimeData();
print_r($realtimeData);
