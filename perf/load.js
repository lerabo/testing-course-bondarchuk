// НФ-продуктивність: GET /api/students для потоку з 300 студентів (data/stream.json)
import http from "k6/http";
import { check } from "k6";

export const options = {
  scenarios: {
    students: {
      executor: "constant-arrival-rate", // відкрита модель: темп не залежить від відповідей
      rate: Number(__ENV.RATE || 20),
      timeUnit: "1s",
      duration: "30s",
      preAllocatedVUs: 20,
      maxVUs: 100,
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<300"],
  },
};

const BASE = __ENV.BASE_URL || "http://127.0.0.1:8000";
const params = {
  headers: { Authorization: "Bearer teacher-token" },
  timeout: "10s",
};

export default function () {
  const res = http.get(`${BASE}/api/students`, params);
  check(res, { "статус 200": (r) => r.status === 200 });
}
