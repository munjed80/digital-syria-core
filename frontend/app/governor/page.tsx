'use client';

import PopulationStatisticsView from '../../components/PopulationStatisticsView';

export default function GovernorPage() {
  return (
    <PopulationStatisticsView
      heading="لوحة المحافظ"
      description="إحصاءات السكان والأسر ضمن نطاق المحافظة. الصلاحيات تُحقَّق في الواجهة الخلفية."
    />
  );
}
