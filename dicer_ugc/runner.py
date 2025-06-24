"""Main pipeline orchestration."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import json

from .config import PipelineConfig
from .models import VariantTask, TaskStatus, TaskResult, RunState
from .variant_matrix import VariantMatrixBuilder
from .utils import (
    generate_run_id, hash_config, ensure_dir, get_output_dir,
    write_manifest, log_progress, log_error, log_success, log_warning,
    log_info, format_cost, format_duration
)


class PipelineRunner:
    """Orchestrates the video generation pipeline."""
    
    def __init__(self, config: PipelineConfig, run_id: Optional[str] = None, max_parallel: int = 3):
        self.config = config
        self.run_id = run_id or generate_run_id()
        self.max_parallel = max_parallel
        
        # Set up directories
        self.output_dir = ensure_dir(get_output_dir(self.run_id))
        self.videos_dir = ensure_dir(self.output_dir / "videos")
        
        # Initialize components
        self.matrix_builder = VariantMatrixBuilder(config)
        self.state: Optional[RunState] = None
        
        # Placeholder for providers (to be implemented)
        self.speech_provider = None
        self.face_provider = None
        self.composer = None
        self.rubric_provider = None
        self.cost_tracker = None
    
    def _save_state(self) -> None:
        """Save current run state."""
        if self.state:
            state_path = self.output_dir / "state.json"
            self.state.save(state_path)
    
    def _load_state(self) -> bool:
        """Load existing run state. Returns True if state was loaded."""
        state_path = self.output_dir / "state.json"
        if state_path.exists():
            self.state = RunState.load(state_path)
            return True
        return False
    
    async def _process_task(self, task: VariantTask) -> TaskResult:
        """Process a single variant task."""
        log_info(f"Processing task {task.task_id}: {task.actor_id} - {task.variant_type.value} v{task.variant_num}")
        
        result = TaskResult(
            task_id=task.task_id,
            status=TaskStatus.IN_PROGRESS,
            start_time=datetime.now()
        )
        
        try:
            # TODO: Implement actual processing steps
            # 1. Generate TTS audio
            # audio_path = await self.speech_provider.generate(task.actor_id, task.script_text)
            # result.outputs['audio'] = audio_path
            # result.costs['tts'] = tts_cost
            
            # 2. Generate face sync video
            # video_path = await self.face_provider.sync(task.actor_id, audio_path)
            # result.outputs['raw_video'] = video_path
            
            # 3. Compose final video
            # final_path = await self.composer.compose(video_path, audio_path, task.script_text)
            # result.outputs['final_video'] = final_path
            
            # 4. Evaluate with rubric
            # rubric_result = await self.rubric_provider.evaluate(final_path)
            # result.outputs['rubric'] = rubric_result
            
            # For now, simulate success
            await asyncio.sleep(1)  # Simulate work
            
            result.status = TaskStatus.COMPLETED
            result.outputs['final_video'] = self.videos_dir / task.output_filename
            result.costs['tts'] = 0.15
            result.costs['rubric'] = 0.06
            
            log_success(f"Completed task {task.task_id}")
            
        except Exception as e:
            result.status = TaskStatus.FAILED
            result.error_message = str(e)
            log_error(f"Failed task {task.task_id}", e)
        
        result.end_time = datetime.now()
        return result
    
    async def _run_tasks_async(self, tasks: List[VariantTask]) -> Dict[str, TaskResult]:
        """Run tasks with controlled parallelism."""
        results = {}
        semaphore = asyncio.Semaphore(self.max_parallel)
        
        async def process_with_semaphore(task: VariantTask):
            async with semaphore:
                result = await self._process_task(task)
                results[task.task_id] = result
                
                # Update state
                if self.state:
                    self.state.task_results[task.task_id] = result
                    if result.status == TaskStatus.COMPLETED:
                        self.state.completed_tasks.append(task.task_id)
                    elif result.status == TaskStatus.FAILED:
                        self.state.failed_tasks.append(task.task_id)
                    self.state.total_cost += result.total_cost
                    
                    # Check cost cap
                    if self.state.total_cost >= self.config.cost_cap:
                        log_warning(f"Cost cap reached: {format_cost(self.state.total_cost)} >= {format_cost(self.config.cost_cap)}")
                        # Cancel remaining tasks
                        return
                    
                    self._save_state()
                    log_progress(
                        len(self.state.completed_tasks) + len(self.state.failed_tasks),
                        self.state.total_tasks,
                        f"Progress (Cost: {format_cost(self.state.total_cost)})"
                    )
        
        # Create all tasks
        aws = [process_with_semaphore(task) for task in tasks]
        
        # Run tasks
        await asyncio.gather(*aws, return_exceptions=True)
        
        return results
    
    def run(self, dry_run: bool = False) -> RunState:
        """Run the complete pipeline."""
        log_info(f"Starting pipeline run: {self.run_id}")
        
        # Build task matrix
        all_tasks = self.matrix_builder.build_matrix()
        
        if dry_run:
            log_info("DRY RUN - Displaying task matrix only")
            self.matrix_builder.display_matrix(all_tasks)
            return RunState(
                run_id=self.run_id,
                config_hash=hash_config(self.config.model_dump()),
                total_tasks=len(all_tasks)
            )
        
        # Initialize state
        self.state = RunState(
            run_id=self.run_id,
            config_hash=hash_config(self.config.model_dump()),
            total_tasks=len(all_tasks)
        )
        
        # Save initial state and config
        self._save_state()
        config_path = self.output_dir / "config.yaml"
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(self.config.model_dump(), f, default=str)
        
        # Display matrix
        self.matrix_builder.display_matrix(all_tasks)
        
        # Run tasks
        log_info(f"Processing {len(all_tasks)} tasks with max {self.max_parallel} parallel")
        asyncio.run(self._run_tasks_async(all_tasks))
        
        # Finalize
        self.state.end_time = datetime.now()
        self._save_state()
        
        # Write manifest
        manifest_data = {
            "run_id": self.run_id,
            "offer_id": self.config.offer_id,
            "total_videos": len(all_tasks),
            "completed": len(self.state.completed_tasks),
            "failed": len(self.state.failed_tasks),
            "total_cost": self.state.total_cost,
            "duration": format_duration(self.state.duration) if self.state.duration else "N/A",
            "videos": [
                {
                    "task_id": task.task_id,
                    "actor_id": task.actor_id,
                    "variant_type": task.variant_type.value,
                    "variant_num": task.variant_num,
                    "filename": task.output_filename,
                    "status": self.state.task_results.get(task.task_id, {}).status.value if task.task_id in self.state.task_results else "pending"
                }
                for task in all_tasks
            ]
        }
        write_manifest(self.output_dir, manifest_data)
        
        # Write cost report
        cost_report = {
            "run_id": self.run_id,
            "total_cost": self.state.total_cost,
            "cost_cap": self.config.cost_cap,
            "providers": {
                "elevenlabs": sum(r.costs.get('tts', 0) for r in self.state.task_results.values()),
                "gemini": sum(r.costs.get('rubric', 0) for r in self.state.task_results.values()),
            },
            "per_video_average": self.state.total_cost / len(self.state.completed_tasks) if self.state.completed_tasks else 0
        }
        with open(self.output_dir / "cost_report.json", 'w') as f:
            json.dump(cost_report, f, indent=2)
        
        # Summary
        log_success(f"Pipeline completed: {self.run_id}")
        log_info(f"Completed: {len(self.state.completed_tasks)}/{self.state.total_tasks}")
        log_info(f"Failed: {len(self.state.failed_tasks)}")
        log_info(f"Total cost: {format_cost(self.state.total_cost)}")
        log_info(f"Duration: {format_duration(self.state.duration) if self.state.duration else 'N/A'}")
        
        return self.state
    
    def resume(self) -> RunState:
        """Resume an interrupted pipeline run."""
        log_info(f"Resuming pipeline run: {self.run_id}")
        
        # Load existing state
        if not self._load_state():
            raise ValueError(f"No state found for run {self.run_id}")
        
        # Verify config hasn't changed
        current_hash = hash_config(self.config.model_dump())
        if current_hash != self.state.config_hash:
            log_warning("Configuration has changed since last run")
        
        # Get remaining tasks
        remaining_tasks = self.matrix_builder.get_resume_tasks(
            self.state.completed_tasks + self.state.failed_tasks
        )
        
        if not remaining_tasks:
            log_info("No remaining tasks to process")
            return self.state
        
        log_info(f"Resuming with {len(remaining_tasks)} remaining tasks")
        
        # Run remaining tasks
        asyncio.run(self._run_tasks_async(remaining_tasks))
        
        # Finalize
        self.state.end_time = datetime.now()
        self._save_state()
        
        log_success(f"Resume completed: {self.run_id}")
        return self.state