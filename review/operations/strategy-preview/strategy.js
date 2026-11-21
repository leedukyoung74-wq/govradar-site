"use strict";

const checklist = document.querySelector("#checklist");
const boxes = [...checklist.querySelectorAll("input[type=checkbox]")];
const storageKey = "wmm-strategy-preview-checklist";
const progress = document.querySelector("#progress");

try {
  const checked = JSON.parse(localStorage.getItem(storageKey));
  if (Array.isArray(checked)) {
    boxes.forEach(box => { box.checked = checked.includes(box.id); });
  }
} catch {
  // Checking items remains available when browser storage is unavailable.
}

function updateChecklist() {
  const checked = boxes.filter(box => box.checked).map(box => box.id);
  progress.textContent = `${boxes.length}개 중 ${checked.length}개 확인`;
  try {
    localStorage.setItem(storageKey, JSON.stringify(checked));
  } catch {
    // The current page still shows the checked items.
  }
}

checklist.addEventListener("change", updateChecklist);
checklist.addEventListener("reset", () => setTimeout(updateChecklist, 0));
updateChecklist();

const actions = {
  manufacturing: ["제조·물류", "핵심 공급사 3곳과 대체 운송 경로를 확인하고, 장애 시 주문·재고를 수기로 처리할 담당자를 정합니다."],
  services: ["전문 서비스·중소기업", "고객 연락과 청구에 쓰는 주요 계정의 다중인증, 접근 권한과 백업 복원을 확인합니다."],
  nonprofit: ["교육·복지·비영리 기관", "돌봄·수업·필수 서비스별 대체 연락, 담당자 인수인계와 안전 공지 채널을 정합니다."],
};
const sector = document.querySelector("#sector");
const action = document.querySelector("#sector-action");

sector.addEventListener("change", () => {
  const [name, advice] = actions[sector.value];
  const label = document.createElement("strong");
  label.textContent = name;
  action.replaceChildren(label, document.createTextNode(" " + advice));
});

const targetTime = document.querySelector("#recovery-target");
const actualTime = document.querySelector("#recovery-actual");
const recoveryResult = document.querySelector("#recovery-result");

function updateRecoveryResult() {
  if (!targetTime.validity.valid || !actualTime.validity.valid) {
    recoveryResult.textContent = "1분에서 10,080분 사이의 정수를 입력하세요.";
    return;
  }
  if (targetTime.value === "" || actualTime.value === "") {
    recoveryResult.textContent = "목표와 실제 소요 시간을 입력하면 결과를 표시합니다.";
    return;
  }
  const minutesOver = actualTime.valueAsNumber - targetTime.valueAsNumber;
  recoveryResult.textContent = minutesOver <= 0
    ? `목표 이내에 복구했습니다. 실제 소요 시간 ${actualTime.valueAsNumber.toLocaleString("ko-KR")}분.`
    : `목표를 ${minutesOver.toLocaleString("ko-KR")}분 초과했습니다. 지연 원인을 확인하고 다시 시험하세요.`;
}

targetTime.addEventListener("input", updateRecoveryResult);
actualTime.addEventListener("input", updateRecoveryResult);
