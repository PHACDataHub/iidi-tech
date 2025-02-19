import React from 'react';
import { GcdsText } from '@cdssnc/gcds-components-react';

const Alert = () => {
  return (
    <div className="alert" style={{  borderColor: '#269abc' }}>
    <GcdsText>
        <span>This system is for synthetic data testing purposes only for IIDI project. No real patient data is used.</span>
      </GcdsText>

    </div>
  );
};

export default Alert;
