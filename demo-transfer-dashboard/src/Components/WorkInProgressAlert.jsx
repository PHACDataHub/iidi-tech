import './WorkInProgressAlert.css';
import {
  GcdsNotice,
  GcdsText,
  GcdsDetails,
} from '@cdssnc/gcds-components-react';
import React from 'react';

const WorkInProgressAlert = () => {
  return (
    <div className="work-in-progress-alert">
      <GcdsNotice
        type="info"
        noticeTitleTag="h2"
        noticeTitle="Work in progress / Travail en cours"
      >
        <GcdsDetails detailsTitle="Disclaimer (EN)">
          <GcdsText>
            The patient records displayed in this PT-to-PT Transfer Dashboard
            are solely for demonstration purposes. All patient data is
            synthetic, with unique patient IDs assigned to avoid duplication and
            data quality issues. However, this demonstration does not include or
            validate re-identification processes, record duplication checks, or
            data quality assurance. The dashboard is not designed to handle or
            address any issues related to patient identification, record
            accuracy, or clinical validation. The sole purpose of this dashboard
            is to showcase data transfer capabilities between British Columbia
            and Ontario without any real-world data governance or validation
            processes in scope.
          </GcdsText>
        </GcdsDetails>
        <GcdsDetails detailsTitle="Avertissement (FR)">
          <GcdsText>
            Les dossiers des patients affichés dans ce tableau de bord de
            transfert PT-à-PT sont uniquement à des fins de démonstration.
            Toutes les données des patients sont synthétiques, avec des
            identifiants uniques attribués pour éviter la duplication et les
            problèmes de qualité des données. Cependant, cette démonstration
            n'inclut pas et ne valide pas les processus de réidentification, les
            vérifications de duplication de dossiers ou l'assurance de la
            qualité des données. Ce tableau de bord n'est pas conçu pour traiter
            ou aborder les questions liées à l'identification des patients, à
            l'exactitude des dossiers ou à la validation clinique. L'objectif
            unique de ce tableau de bord est de présenter les capacités de
            transfert de données entre la Colombie-Britannique et l'Ontario,
            sans que les processus réels de gouvernance des données ou de
            validation soient inclus dans la portée.
          </GcdsText>
        </GcdsDetails>
      </GcdsNotice>
    </div>
  );
};

export default WorkInProgressAlert;
