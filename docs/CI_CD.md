# CI/CD Pipeline Documentation

## Обзор

Проектът използва GitHub Actions за автоматизация на тестване, качествен контрол, security scanning, Docker build и deployment.

## Workflows

### 1. CI Pipeline ([.github/workflows/ci.yml](../.github/workflows/ci.yml))

Основният CI workflow който се изпълнява при всеки push и pull request към `main` и `develop` клонове, както и ежедневно в 2:00 UTC.

#### Jobs:

##### **Test Job**
- Тестване на Python 3.11 и 3.12
- Инсталация на зависимости с pip cache
- Flake8 linting за syntax errors
- Black code formatting проверка
- Pytest с code coverage (минимум 60%)
- Upload на coverage reports към Codecov
- Upload на HTML coverage report като artifact

**Triggers:**
- Push към main/develop
- Pull requests към main/develop
- Scheduled: всеки ден в 02:00 UTC

**Requirements:**
- Coverage threshold: ≥60%
- Всички критични тестове трябва да минават

##### **Lint Job**
- Code formatting проверка с Black
- Import sorting с isort
- Style guide enforcement с flake8
- Type checking с mypy

**Статус:** Non-blocking (continue-on-error)

##### **Security Job**
- Bandit security linting за common vulnerabilities
- Safety dependency scanning за vulnerable packages
- Upload на security reports като artifacts

**Outputs:**
- `bandit-report.json` - Detailed security findings

##### **Docker Job**
- Зависи от: test, lint, security jobs
- Изпълнява се само при push към main/develop
- Docker Buildx setup за multi-platform builds
- Metadata extraction за tagging
- Docker build с GitHub Actions cache

**Tags:**
- `latest` - само за main branch
- `{branch}-{sha}` - за всеки push
- `{branch}` - branch name

---

### 2. Deployment Pipeline ([.github/workflows/deploy.yml](../.github/workflows/deploy.yml))

Production deployment workflow с PostgreSQL и Redis services.

#### Jobs:

##### **Test Job (with Services)**
- PostgreSQL 15 service container
- Redis 7 service container
- Health checks за services
- Full integration testing
- Coverage reporting

**Environment Variables:**
- `DATABASE_URL`: PostgreSQL connection
- `REDIS_HOST`: Redis connection
- `ENVIRONMENT`: testing

##### **Build Job**
- Изпълнява се само при push към `production` branch
- Docker build and push към GitHub Container Registry (ghcr.io)
- Multi-platform support
- Registry cache optimization

**Permissions Required:**
- `contents: read`
- `packages: write`

**Registry:** GitHub Container Registry (ghcr.io)

##### **Deploy Job**
- SSH deployment към VPS
- Zero-downtime deployment strategy
- Alembic database migrations
- Health check след deployment
- Docker image cleanup
- Slack notifications (success/failure)

**Required Secrets:**
- `VPS_HOST` - Production server hostname
- `VPS_USER` - SSH username
- `VPS_SSH_KEY` - SSH private key
- `SLACK_WEBHOOK` - Slack notification webhook

**Deployment Steps:**
1. Git pull latest code
2. Docker Compose pull images
3. Rolling update на API service
4. Database migrations
5. Health check (http://localhost:8000/health)
6. Cleanup old images

---

## Required Secrets

### GitHub Secrets Setup

За да работят workflows правилно, конфигурирайте следните secrets в GitHub:

#### Optional (за CI):
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password/token
- `CODECOV_TOKEN` - Codecov upload token

#### Required (за Production Deployment):
- `VPS_HOST` - IP адрес или hostname на production сървъра
- `VPS_USER` - SSH потребителско име
- `VPS_SSH_KEY` - SSH private key за authentication
- `SLACK_WEBHOOK` - Webhook URL за Slack нотификации
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions

### Как да добавите secrets:
1. Отворете Settings → Secrets and variables → Actions
2. Натиснете "New repository secret"
3. Добавете името и стойността

---

## Branch Strategy

### `main` branch
- Stable production-ready code
- CI runs на всеки push
- Docker build (но не push)
- Protected branch - изисква PR review

### `develop` branch
- Active development
- CI runs на всеки push
- Docker build за testing
- Може да се merge директно

### `production` branch
- Production deployment trigger
- Изисква успешен CI от main
- Автоматичен deployment към VPS
- Protected branch

---

## Coverage Reports

### Codecov Integration
Coverage reports се качват автоматично към Codecov при всеки CI run.

**Threshold:** Минимум 60% code coverage

**Reports:**
- XML report → Codecov
- HTML report → GitHub Artifacts
- Terminal output → GitHub Actions logs

### Как да видите coverage:
1. **GitHub Actions:** Artifacts → "coverage-report"
2. **Codecov:** codecov.io/gh/{username}/gpu-price-tracker
3. **Локално:** `pytest --cov=. --cov-report=html && open htmlcov/index.html`

---

## Security Scanning

### Bandit
Сканира кода за common security issues:
- SQL injection vulnerabilities
- Hardcoded passwords
- Unsafe deserialization
- Shell injection risks

### Safety
Проверява dependencies за known vulnerabilities от PyPI safety database.

**Reports:** Security artifacts в GitHub Actions

---

## Docker Build Process

### Multi-stage Build
Използва се multi-stage Dockerfile за оптимизация:
1. **Builder stage:** Инсталация на dependencies
2. **Runtime stage:** Минимален production image

### Caching Strategy
- GitHub Actions cache за по-бързи builds
- Layer caching за dependencies
- Build cache optimization

### Build Arguments
- `BUILDTIME` - Timestamp на build
- `VERSION` - Git SHA

---

## Local Development

### Пускане на CI локално

```bash
# Тестване
pytest tests/ --cov=. --cov-report=term -v

# Linting
black --check .
isort --check-only .
flake8 . --max-line-length=127

# Security
bandit -r . -ll
safety check

# Docker build
docker build -t gpu-price-tracker:local .
```

### Pre-commit Hooks

Препоръчително е да използвате pre-commit hooks за автоматични проверки:

```bash
# .git/hooks/pre-commit
#!/bin/bash
black --check . || exit 1
isort --check-only . || exit 1
pytest tests/ || exit 1
```

---

## Troubleshooting

### CI Failures

#### Coverage под threshold
```bash
# Проверете coverage локално
pytest --cov=. --cov-report=term-missing

# Добавете тестове за непокрити файлове
```

#### Docker build failure
```bash
# Проверете Dockerfile синтаксис
docker build -t test .

# Проверете requirements.txt
pip install -r requirements.txt
```

#### Security issues
```bash
# Прегледайте bandit report
bandit -r . -ll -f screen

# Поправете уязвимости
# Обновете зависимости
pip install --upgrade -r requirements.txt
```

### Deployment Failures

#### SSH Connection Failed
- Проверете VPS_HOST, VPS_USER, VPS_SSH_KEY secrets
- Уверете се че SSH key е правилен формат (без passphrase)

#### Database Migration Failed
```bash
# SSH към сървъра
ssh user@server

# Проверете migration status
docker-compose exec api alembic current

# Ръчен migration
docker-compose exec api alembic upgrade head
```

#### Health Check Failed
```bash
# Проверете логове
docker-compose logs api

# Проверете health endpoint
curl http://localhost:8000/health
```

---

## Best Practices

### 1. **Commit Messages**
Използвайте conventional commits за автоматично versioning:
```
feat: добавена нова функционалност
fix: поправен bug
docs: обновена документация
test: добавени тестове
refactor: code refactoring
```

### 2. **Pull Requests**
- Минимум 1 approval преди merge
- CI трябва да мине успешно
- Coverage не трябва да пада
- Security scan не трябва да показва критични проблеми

### 3. **Testing**
- Пишете unit tests за нова функционалност
- Integration tests за API endpoints
- Поддържайте coverage над 60%

### 4. **Security**
- Никога не commit-вайте secrets в кода
- Използвайте environment variables
- Regular dependency updates
- Прегледайте security reports

---

## Monitoring

### GitHub Actions Dashboard
- Вижте status на workflows: Actions tab
- Download artifacts: Coverage reports, security scans
- Re-run failed jobs при нужда

### Deployment Monitoring
- Slack notifications за deployment status
- Health check endpoint: `/health`
- Application logs: `docker-compose logs -f api`

---

## Future Improvements

- [ ] Automated dependency updates (Dependabot)
- [ ] Performance benchmarking в CI
- [ ] Load testing преди production deployment
- [ ] Automated rollback при failed health check
- [ ] Multi-environment deployment (staging, production)
- [ ] Canary deployments
- [ ] Integration с error tracking (Sentry)

---

## Contact

За въпроси относно CI/CD setup:
- Проверете GitHub Actions logs
- Прегледайте този документ
- Създайте issue в repository-то
