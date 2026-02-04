import { PactV3, MatchersV3 } from '@pact-foundation/pact';
import path from 'path';
import { InsulinClient } from '../src/insulinClient';

const { string, number, eachLike, like, boolean } = MatchersV3;

const provider = new PactV3({
  consumer: 'InsulinClient',
  provider: 'RiskAlgoService',
  dir: path.resolve(process.cwd(), '../pacts'),
  logLevel: 'warn',
});

describe('RiskAlgoService Contract Tests', () => {
  it('should return healthy status', async () => {
    await provider
      .given('the service is healthy')
      .uponReceiving('a GET request to /health')
      .withRequest({
        method: 'GET',
        path: '/health',
      })
      .willRespondWith({
        status: 200,
        body: like({
          status: 'healthy',
          service: 'RiskAlgoService',
          version: '1.0.0',
        }),
      });

    await provider.executeTest(async (mockServer) => {
      const client = new InsulinClient(mockServer.url);
      const response = await client.healthCheck();
      expect(response.status).toBe('healthy');
    });
  });

  it('should calculate bolus dosage', async () => {
    await provider
      .given('a valid patient and glucose data')
      .uponReceiving('a POST request to /calculate/bolus')
      .withRequest({
        method: 'POST',
        path: '/calculate/bolus',
        body: like({
          patient_id: string('patient-123'),
          current_glucose_mg_dl: number(150),
          carbs_grams: number(30),
          insulin_on_board_units: number(5),
        }),
      })
      .willRespondWith({
        status: 200,
        body: like({
          patient_id: string('patient-123'),
          recommended_bolus_units: number(10),
          correction_units: number(5),
          carb_coverage_units: number(3),
          risk_level: string('low'),
          warnings: eachLike(string('warning-1'), 0),
        }),
      });

    await provider.executeTest(async (mockServer) => {
      const client = new InsulinClient(mockServer.url);
      const response = await client.calculateBolus({
        patient_id: 'patient-123',
        current_glucose_mg_dl: 150,
        carbs_grams: 30,
        insulin_on_board_units: 5,
      });
      expect(response.patient_id).toBe('patient-123');
      expect(response.recommended_bolus_units).toBeGreaterThan(0);
    });
  });

  it('should calculate basal rate adjustment', async () => {
    await provider
      .given('a valid patient and glucose readings')
      .uponReceiving('a POST request to /calculate/basal-adjustment')
      .withRequest({
        method: 'POST',
        path: '/calculate/basal-adjustment',
        body: like({
          patient_id: string('patient-123'),
          glucose_readings: eachLike(number(100), 6),
          current_basal_rate: number(10),
        }),
      })
      .willRespondWith({
        status: 200,
        body: like({
          patient_id: string('patient-123'),
          adjusted_basal_rate: number(10),
          adjustment_percentage: number(0),
          trend: string('stable'),
          action: string('maintain'),
        }),
      });

    await provider.executeTest(async (mockServer) => {
      const client = new InsulinClient(mockServer.url);
      const response = await client.calculateBasalAdjustment({
        patient_id: 'patient-123',
        glucose_readings: [100, 110, 120, 130, 140, 150],
        current_basal_rate: 10,
      });
      expect(response.patient_id).toBe('patient-123');
      expect(response.adjusted_basal_rate).toBeGreaterThan(0);
    });
  });
});