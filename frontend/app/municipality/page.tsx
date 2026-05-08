'use client';

import PopulationStatisticsView from '../../components/PopulationStatisticsView';

export default function MunicipalityPage() {
  return (
    <PopulationStatisticsView
      heading="لوحة رئيس البلدية"
      description="إحصاءات السكان والأسر ضمن نطاق البلدية. الصلاحيات تُحقَّق في الواجهة الخلفية."
    />
  );
}
