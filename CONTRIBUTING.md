# Contributing Guide

## Branch Flow

개인 브랜치 → dev → main

## Rules

1. 각자 자기 개인 브랜치에서 작업한다.
2. 개인 브랜치끼리 직접 merge하지 않는다.
3. 개인 브랜치는 dev로 Pull Request를 생성한다.
4. dev에서 통합 검증을 완료한 뒤 main으로 Pull Request를 생성한다.
5. main과 dev에 직접 push하지 않는다.
6. `.env`, 의료 데이터, 모델 체크포인트를 커밋하지 않는다.

## Commit Message

- `feat:` 새로운 기능
- `fix:` 오류 수정
- `refactor:` 코드 구조 개선
- `test:` 테스트
- `docs:` 문서
- `chore:` 환경설정 및 기타 작업
