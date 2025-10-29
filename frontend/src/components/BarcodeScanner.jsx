import { useEffect, useRef, useState } from 'react';
import { Html5Qrcode } from 'html5-qrcode';
import { Button } from '@/components/ui/button';
import { X, Scan } from 'lucide-react';

const BarcodeScanner = ({ onScanSuccess, onClose }) => {
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState(null);
  const scannerRef = useRef(null);
  const html5QrCodeRef = useRef(null);

  useEffect(() => {
    return () => {
      stopScanner();
    };
  }, []);

  const startScanner = async () => {
    try {
      setError(null);
      setScanning(true);

      html5QrCodeRef.current = new Html5Qrcode("barcode-reader");

      const config = {
        fps: 10,
        qrbox: { width: 250, height: 150 },
        aspectRatio: 1.0,
      };

      await html5QrCodeRef.current.start(
        { facingMode: "environment" },
        config,
        (decodedText) => {
          onScanSuccess(decodedText);
          stopScanner();
          onClose();
        },
        (errorMessage) => {
          // Silent errors during scanning
        }
      );
    } catch (err) {
      console.error("Error starting scanner:", err);
      setError("Gagal mengakses kamera. Pastikan izin kamera sudah diaktifkan.");
      setScanning(false);
    }
  };

  const stopScanner = async () => {
    if (html5QrCodeRef.current) {
      try {
        await html5QrCodeRef.current.stop();
        html5QrCodeRef.current = null;
      } catch (err) {
        console.error("Error stopping scanner:", err);
      }
    }
    setScanning(false);
  };

  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg p-6 max-w-md w-full space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Scan className="h-5 w-5" />
            Scan Barcode/QR
          </h3>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => {
              stopScanner();
              onClose();
            }}
            data-testid="close-scanner"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        <div id="barcode-reader" className="w-full"></div>

        {error && (
          <div className="p-3 bg-red-50 text-red-600 rounded-lg text-sm">
            {error}
          </div>
        )}

        {!scanning && !error && (
          <Button
            onClick={startScanner}
            className="w-full"
            data-testid="start-scanner-btn"
          >
            <Scan className="h-4 w-4 mr-2" />
            Mulai Scan
          </Button>
        )}

        {scanning && (
          <Button
            onClick={stopScanner}
            variant="destructive"
            className="w-full"
            data-testid="stop-scanner-btn"
          >
            Hentikan Scan
          </Button>
        )}

        <p className="text-xs text-center text-gray-500">
          Arahkan kamera ke barcode atau QR code produk
        </p>
      </div>
    </div>
  );
};

export default BarcodeScanner;
