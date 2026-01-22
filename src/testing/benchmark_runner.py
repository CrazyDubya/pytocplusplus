import subprocess
import sys
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("BenchmarkRunner")

class BenchmarkRunner:
    """Runs benchmarks comparing Python and C++ implementations."""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
    
    def run_benchmarks(self, output_dir: Path, benchmark_script: Path) -> str:
        """Run benchmarks and return the report."""
        output_dir = Path(output_dir)
        benchmark_script = Path(benchmark_script)
        
        # First build the C++ code
        if not self._build_cpp_implementation(output_dir):
            return "❌ Failed to run benchmarks due to build errors"
        
        # Then run the benchmark script
        try:
            # Run the benchmark script with the output directory as an argument
            cmd = [sys.executable, str(benchmark_script), str(output_dir)]
            result = subprocess.run(cmd, 
                                   capture_output=True, 
                                   text=True, 
                                   check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running benchmark script: {e}")
            return f"❌ Benchmark error: {e.stderr}"
        except Exception as e:
            logger.error(f"Unexpected error running benchmarks: {e}")
            return f"❌ Benchmark error: {str(e)}"
    
    def _build_cpp_implementation(self, output_dir: Path) -> bool:
        """Build the C++ implementation."""
        try:
            logger.info("Building C++ implementation...")
            
            # Create build directory if it doesn't exist
            build_dir = output_dir / "build"
            build_dir.mkdir(exist_ok=True)
            
            # Run CMake
            cmake_cmd = ["cmake", "..", "-DCMAKE_BUILD_TYPE=Release"]
            subprocess.run(cmake_cmd, 
                          cwd=build_dir, 
                          check=True, 
                          stderr=subprocess.PIPE, 
                          stdout=subprocess.PIPE)
            
            # Run make
            make_cmd = ["make", "-j4"]
            subprocess.run(make_cmd, 
                          cwd=build_dir, 
                          check=True, 
                          stderr=subprocess.PIPE, 
                          stdout=subprocess.PIPE)
            
            # Copy the built module to the python_wrapper directory
            python_wrapper_dir = output_dir / "python_wrapper"
            if not python_wrapper_dir.exists():
                logger.warning(f"Python wrapper directory not found at {python_wrapper_dir}")
                return False
            
            # Find the built module file
            import glob
            module_files = list(build_dir.glob("cpp_impl*.so"))
            if not module_files:
                logger.error("No compiled module found in build directory")
                return False
                
            import shutil
            # Copy the module to the python_wrapper directory
            for module_file in module_files:
                target_path = python_wrapper_dir / module_file.name
                logger.info(f"Copying {module_file} to {target_path}")
                shutil.copy(module_file, target_path)
            
            logger.info("✅ C++ implementation built and installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error building C++ implementation: {e}")
            logger.error(f"Command output: {e.stderr.decode() if e.stderr else ''}")
            print(f"❌ Error building C++ implementation: {e.stderr.decode() if e.stderr else ''}")
            print("❌ Failed to build C++ implementation")
            return False
        except Exception as e:
            logger.error(f"Unexpected error building C++ implementation: {e}")
            print(f"❌ Error building C++ implementation: {str(e)}")
            print("❌ Failed to build C++ implementation")
            return False