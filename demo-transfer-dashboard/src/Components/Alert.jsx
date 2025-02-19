import React from 'react';
import { GcdsNotice, GcdsText } from '@cdssnc/gcds-components-react';

const Alert = () => {
  return (
    <div className="alert">
      <GcdsNotice
        type="info"
        noticeTitleTag="h2"
        noticeTitle="Work in progress"
      >
        <GcdsText>
          {' '}
          This system is for synthetic data testing purposes only for IIDI
          project. No real patient data is used.
        </GcdsText>
      </GcdsNotice>
    </div>
  );
};

export default Alert;
