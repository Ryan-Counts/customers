import APIService from '../APIService';
import { useState } from 'react';

function ImportPanel() {
  const [importResult, setImportResult] = useState(null);

  const handleImportEmail = async () => {
    setImportResult(null);
    try {
      const response = await APIService.importCustomersEmail();
      setImportResult({
        success: response.success,
        message: response.message
      });
    } catch (error) {
      setImportResult({
        success: false,
        message: 'Error importing customers: ' + error.message
      });
    }
  };

  const handleImportDB = async () => {
    setImportResult(null);
    try {
      const response = await APIService.importCustomersDB();
      setImportResult({
        success: response.success,
        message: response.message
      });
    } catch (error) {
      setImportResult({
        success: false,
        message: 'Error importing customers: ' + error.message
      });
    }
  };

  const handleImportCSV = () => {
    setImportResult(null);
    APIService.importCustomersCSV()
    .then((response) => 
      setImportResult({
        success: response.success,
        message: response.message
      })
    )    .catch((error) => 
      setImportResult({
        success: false,
        message: 'Error importing customers: ' + error.message
      })
    );
  }

    return (
        <div className="import-panel">
            <h2>Import Customers</h2>
            <button onClick={handleImportEmail}>
                Import from Email
            </button>
            <button onClick={handleImportDB}>
                Import from Database
            </button>
            <button onClick={handleImportCSV}>
                Import from CSV
            </button>
            {importResult && (
              <p className={importResult.success ? 'success' : 'error'}>
                {importResult.message}
              </p>
            )}
          </div>
        );
}

export default ImportPanel;