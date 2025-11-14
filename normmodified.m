clear all
close all
clc;
rootFolder = 'C:\POWER\';

for subjIdx = 1:7
    subjName = sprintf('NSFSubject%02d', subjIdx);
    emgFolder = fullfile(rootFolder, subjName, 'EMG_Processed');
    normFolder = fullfile(rootFolder, subjName, 'normmod_emg');
    if ~exist(emgFolder, 'dir')
        warning(['Missing folder: ', emgFolder]);
        continue;
    end
    if ~exist(normFolder, 'dir')
        mkdir(normFolder);
    end
    fprintf('\n======= Processing %s =======\n', subjName);

    csvPattern = sprintf('NSF_UBT_%02d_*.csv', subjIdx);
    csvFiles = dir(fullfile(emgFolder, csvPattern));
    
    % --- Step 1: find global max per sensor across all files ---
    sensorMaxMap = containers.Map; % key: sensor name, value: max value
    
    for i = 1:length(csvFiles)
        filepath = fullfile(emgFolder, csvFiles(i).name);
        T = readtable(filepath);
        varNames = T.Properties.VariableNames;
        emgCols = varNames(contains(varNames, 'Sensor_') & contains(varNames, 'EMG'));
        
        for k = 1:length(emgCols)
            col = emgCols{k};
            colData = double(T.(col));
            colData(isnan(colData) | isinf(colData)) = 0;
            maxVal = max(colData);
            
            if isKey(sensorMaxMap, col)
                sensorMaxMap(col) = max(sensorMaxMap(col), maxVal);
            else
                sensorMaxMap(col) = maxVal;
            end
        end
    end

    % Print the global max values for this subject
    sensorKeys = keys(sensorMaxMap);
    fprintf('Global max values for %s:\n', subjName);
    for idx = 1:length(sensorKeys)
        key = sensorKeys{idx};
        fprintf('  %s: %.10f\n', key, sensorMaxMap(key));
    end
    fprintf('\n');
    
    % --- Step 2: normalize each file using global max per sensor ---
    for i = 1:length(csvFiles)
        filepath = fullfile(emgFolder, csvFiles(i).name);
        T = readtable(filepath);
        varNames = T.Properties.VariableNames;
        emgCols = varNames(contains(varNames, 'Sensor_') & contains(varNames, 'EMG'));
        
        for k = 1:length(emgCols)
            col = emgCols{k};
            colData = double(T.(col));
            colData(isnan(colData) | isinf(colData)) = 0;
            
            if isKey(sensorMaxMap, col)
                globalMax = sensorMaxMap(col);
                if globalMax > 0
                    T.(col) = colData / globalMax;
                    % Print max normalized value in this file for this sensor
                    maxNormVal = max(T.(col));
                    %fprintf('File %s - %s max normalized: %.10f\n', csvFiles(i).name, col, maxNormVal);
                else
                    warning('Global max for %s is zero or negative, skipping normalization', col);
                end
            else
                warning('No global max found for %s, skipping normalization', col);
            end
        end
        
        writetable(T, fullfile(normFolder, csvFiles(i).name));
    end
    
    fprintf('Normalized files saved in folder: %s\n', normFolder);
end

disp('All subjects processed with global max normalization per sensor.');

% --- Plotting H, M, L 4,6,12 for subjects 1 to 7 ---
positions = {'H', 'M', 'L'};
numbers = [4, 6, 12];

for subjIdx = 1:7
    subjName = sprintf('NSFSubject%02d', subjIdx);
    normFolder = fullfile(rootFolder, subjName, 'normmod_emg');
    
    for p = 1:length(positions)
        pos = positions{p};
        for n = 1:length(numbers)
            num = numbers(n);
            filename = sprintf('NSF_UBT_%02d_%s_%d.csv', subjIdx, pos, num);
            filepath = fullfile(normFolder, filename);
            
            if ~exist(filepath, 'file')
                warning('File %s not found. Skipping plot.', filename);
                continue;
            end
            
            T = readtable(filepath);
            varNames = T.Properties.VariableNames;
            emgCols = varNames(contains(varNames, 'Sensor_') & contains(varNames, 'EMG'));
            
            figure;
            hold on;
            colors = lines(length(emgCols));
            for k = 1:length(emgCols)
                col = emgCols{k};
                plot(T.Time, T.(col), 'Color', colors(k,:), ...
                    'DisplayName', col, 'LineWidth', 1.2);
            end
            legend(emgCols, 'Location', 'best', 'Interpreter', 'none');
            title(filename(1:end-4), 'Interpreter', 'none');
            xlabel('Time (s)');
            ylabel('Normalized EMG Signal');
            grid on;
            hold off;
        end
    end
end
