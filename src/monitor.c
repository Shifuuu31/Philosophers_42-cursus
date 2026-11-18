/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   monitor.c                                          :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: asaadane <asaadane@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/01/02 23:03:57 by asaadane          #+#    #+#             */
/*   Updated: 2026/11/18 19:43:00 by asaadane         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "philo.h"

// Check if all philosophers have completed the required number of meals
static int	is_finished(t_philo *info)
{
	int	i;

	i = 0;
	while (i < info->n_philo)
	{
		if (info->philo[i].eating_time < info->nbr_meals)
			break ;
		i++;
		if (i > info->n_philo - 1)
			return (1);
	}
	return (0);
}

// Supervisor loop monitoring death times and meal completions
int	check_philos(t_philo *info)
{
	int	i;

	while (1)
	{
		pthread_mutex_lock(&info->sync);
		i = -1;
		while (++i < info->n_philo)
		{
			if (ft_time() - info->philo[i].last_meal > info->t_die)
			{
				manage_philos(&info->philo[i], DIE);
				return (0);
			}
		}
		if (info->philo_eaft_time && is_finished(info))
		{
			pthread_mutex_unlock(&info->sync);
			return (0);
		}
		pthread_mutex_unlock(&info->sync);
		usleep(1000);
	}
	return (0);
}
