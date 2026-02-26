import pytest
from anyio import Path
from fastapi import HTTPException

from api import get_report


@pytest.fixture(scope='module')
async def setup_reports_dir():
	# Ensure reports directory exists before tests run
	p = Path('reports')
	if not await p.exists():
		await p.mkdir()
	yield 'reports'


@pytest.mark.asyncio
async def test_get_report_valid(setup_reports_dir):
	filename = 'valid_report.txt'
	filepath = Path(setup_reports_dir) / filename
	await filepath.write_text('Safe content', encoding='utf-8')

	result = await get_report(filename)
	assert result['content'] == 'Safe content'

	# Cleanup
	if await filepath.exists():
		await filepath.unlink()


@pytest.mark.asyncio
async def test_get_report_traversal(setup_reports_dir):
	# Try to access api.py which is in parent directory
	# We test various traversal payloads that represent decoded paths
	payloads = ['../api.py', '/etc/passwd', '/app/api.py']

	for payload in payloads:
		with pytest.raises(HTTPException) as excinfo:
			await get_report(payload)
		assert excinfo.value.status_code == 403, f'Payload {payload} failed to raise 403'
		assert excinfo.value.detail == 'Acesso negado: O caminho solicitado é inválido.'


@pytest.mark.asyncio
async def test_get_report_not_found(setup_reports_dir):
	filename = 'non_existent_report_12345.txt'
	with pytest.raises(HTTPException) as excinfo:
		await get_report(filename)
	assert excinfo.value.status_code == 404
	assert excinfo.value.detail == 'Relatório não encontrado.'
