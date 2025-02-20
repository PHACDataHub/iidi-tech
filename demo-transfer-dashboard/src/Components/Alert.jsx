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
          Disclaimer (EN): This web interface is temporary and serves as a Proof
          of Concept (POC) to facilitate current technical development and
          testing. It is not intended for production use. Full production
          considerations, including bilingual and WCAG compliance, are in
          progress.
        </GcdsText>
        <GcdsText>
          Avis (FR) : Cette interface web est temporaire et sert de Preuve de
          Concept (POC) pour faciliter les développements techniques actuels et
          les tests. Elle n'est pas destinée à un usage en production. Les
          considérations complètes de production, y compris la conformité
          bilingue et WCAG, sont en cours.
        </GcdsText>
      </GcdsNotice>
    </div>
  );
};

export default Alert;
