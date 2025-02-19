import React from 'react';
import { GcdsNotice, GcdsText } from '@cdssnc/gcds-components-react';

const Alert = () => {
  return (
    <div className="alert">
      <GcdsNotice
        type="info"
        noticeTitleTag="h2"
        noticeTitle="Work in progress / Travail en cours"
      >
        <GcdsText>
          This system is for synthetic data testing purposes only for IIDI
          project. No real patient data is used.
        </GcdsText>
        <GcdsText>
          Ce système est destiné uniquement à des fins de test de données
          synthétiques pour le projet IIDI. Aucune donnée réelle de patient
          n'est utilisée.
        </GcdsText>
      </GcdsNotice>
    </div>
  );
};

export default Alert;
